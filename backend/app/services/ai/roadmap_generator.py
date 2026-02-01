"""
Roadmap Generator - AI-powered learning path generation
"""

import logging
from datetime import date, timedelta
from typing import Dict, Any, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...models.roadmap import Roadmap, RoadmapTask
from ...models.profile import UserProfile
from .llm_client import get_llm_client
from .skill_analyzer import SkillAnalyzer

logger = logging.getLogger(__name__)


class RoadmapGenerator:
    """AI-powered learning roadmap generator."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_client()
        self.skill_analyzer = SkillAnalyzer(db)
    
    async def generate_roadmap(
        self,
        user_id: UUID,
        target_role: str,
        duration_weeks: int = 12,
        intensity: str = "medium"
    ) -> Roadmap:
        """
        Generate a personalized learning roadmap.
        Duration is dynamically calculated based on role complexity.
        """
        logger.info(f"Starting roadmap generation for user {user_id}")
        logger.info(f"Input target_role: '{target_role}', requested duration: {duration_weeks} weeks, intensity: {intensity}")
        
        # Get user profile first
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        if profile:
            logger.info(f"Found user profile - goal_role: '{profile.goal_role}', experience: '{profile.experience_level}'")
        else:
            logger.warning(f"No user profile found for user {user_id}")
        
        # Validate and resolve target_role
        if not target_role or target_role.strip() == "" or target_role.lower() == "none":
            logger.info("Target role not provided in request, checking profile...")
            if profile and profile.goal_role and profile.goal_role.lower() != "none":
                target_role = profile.goal_role
                logger.info(f"Using goal_role from profile: '{target_role}'")
            else:
                raise ValueError(
                    "Target role is required. Please complete your profile with your career goal first."
                )
        
        logger.info(f"Final target_role for roadmap: '{target_role}'")
        
        # DYNAMIC DURATION: Calculate optimal weeks based on role complexity
        optimal_weeks = self._calculate_optimal_duration(target_role, profile)
        duration_weeks = optimal_weeks
        logger.info(f"Calculated optimal duration for {target_role}: {duration_weeks} weeks")
        
        # Get skill gap analysis
        skill_analysis = await self.skill_analyzer.analyze_skill_gap(
            user_id, target_role
        )
        logger.info(f"Skill analysis: missing={len(skill_analysis.get('missing_skills', []))}, "
                   f"to_improve={len(skill_analysis.get('skills_to_improve', []))}")
        
        # Determine daily time based on intensity and profile
        daily_minutes = self._get_daily_minutes(intensity, profile)
        logger.info(f"Daily learning time: {daily_minutes} minutes")
        
        # Generate roadmap structure using AI
        roadmap_data = await self._generate_roadmap_structure(
            target_role=target_role,
            duration_weeks=duration_weeks,
            daily_minutes=daily_minutes,
            skill_analysis=skill_analysis,
            experience_level=profile.experience_level if profile else "beginner",
            learning_style=profile.preferred_learning_style if profile else "mixed"
        )
        
        logger.info(f"Generated roadmap data with title: {roadmap_data.get('roadmap_title', 'N/A')}")
        
        # Create roadmap in database
        roadmap = Roadmap(
            user_id=user_id,
            title=roadmap_data.get("roadmap_title", f"{target_role} Learning Path"),
            description=roadmap_data.get("description", ""),
            target_role=target_role,
            total_weeks=duration_weeks,
            start_date=date.today(),
            end_date=date.today() + timedelta(weeks=duration_weeks),
            status="active",
            milestones=roadmap_data.get("milestones", []),
            generation_params={
                "intensity": intensity,
                "daily_minutes": daily_minutes
            }
        )
        
        self.db.add(roadmap)
        await self.db.flush()
        
        # Create tasks
        weekly_breakdown = roadmap_data.get("weekly_breakdown", [])
        for week_data in weekly_breakdown:
            week_num = week_data.get("week_number", 1)
            days = week_data.get("days", [])
            
            for day_data in days:
                day_num = day_data.get("day_number", 1)
                tasks = day_data.get("tasks", [])
                
                for order, task_data in enumerate(tasks, 1):
                    task = RoadmapTask(
                        roadmap_id=roadmap.id,
                        week_number=week_num,
                        day_number=day_num,
                        order_in_day=order,
                        task_title=task_data.get("title", "Learning Task"),
                        task_description=task_data.get("description", ""),
                        task_type=task_data.get("task_type", "reading"),
                        estimated_duration=task_data.get("estimated_duration", 60),
                        difficulty=task_data.get("difficulty", 3),
                        learning_objectives=task_data.get("learning_objectives", []),
                        success_criteria=task_data.get("success_criteria", ""),
                        prerequisites=task_data.get("prerequisites", []),
                        resources=task_data.get("resources", []),
                        status="pending"
                    )
                    self.db.add(task)
        
        await self.db.commit()
        
        # Refresh with tasks
        result = await self.db.execute(
            select(Roadmap)
            .options(selectinload(Roadmap.tasks))
            .where(Roadmap.id == roadmap.id)
        )
        return result.scalar_one()
    
    async def _generate_roadmap_structure(
        self,
        target_role: str,
        duration_weeks: int,
        daily_minutes: int,
        skill_analysis: Dict[str, Any],
        experience_level: str,
        learning_style: str
    ) -> Dict[str, Any]:
        """Generate roadmap structure using AI."""
        
        logger.info(f"Generating roadmap for target_role: {target_role}")
        logger.info(f"Parameters: duration={duration_weeks} weeks, daily_minutes={daily_minutes}, experience={experience_level}")
        
        # Get skills to learn based on target role
        missing_skills = [s["skill_name"] for s in skill_analysis.get("missing_skills", [])]
        skills_to_improve = [s["skill_name"] for s in skill_analysis.get("skills_to_improve", [])]
        
        # If no skills analysis available, generate role-specific skills
        if not missing_skills:
            missing_skills = self._get_default_skills_for_role(target_role)
            logger.info(f"Using default skills for {target_role}: {missing_skills}")
        
        # Generate roadmap in phases for better quality
        all_weeks = []
        milestones = []
        
        # Define learning phases based on duration
        phases = self._define_learning_phases(target_role, duration_weeks, missing_skills, experience_level)
        
        # Generate each phase with AI
        for phase in phases:
            phase_weeks = await self._generate_phase_weeks(
                target_role=target_role,
                phase=phase,
                daily_minutes=daily_minutes,
                experience_level=experience_level,
                learning_style=learning_style,
                all_skills=missing_skills + skills_to_improve
            )
            all_weeks.extend(phase_weeks.get("weeks", []))
            milestones.extend(phase_weeks.get("milestones", []))
        
        return {
            "roadmap_title": f"Your Path to Becoming a {target_role}",
            "description": f"A personalized {duration_weeks}-week learning journey designed for {experience_level} level learners. "
                          f"This comprehensive roadmap will guide you through mastering: {', '.join(missing_skills[:5])}.",
            "weekly_breakdown": all_weeks,
            "milestones": milestones
        }
    
    def _calculate_optimal_duration(self, target_role: str, profile: Optional[UserProfile]) -> int:
        """Calculate optimal roadmap duration based on role complexity and user profile."""
        role_lower = target_role.lower()
        
        # Role complexity mapping (weeks needed)
        role_durations = {
            # Simple roles (4-6 weeks)
            "excel": 4, "excel specialist": 4, "spreadsheet": 4,
            "data entry": 4, "office assistant": 4,
            "wordpress": 5, "blogger": 4,
            
            # Basic roles (6-8 weeks)
            "html css": 6, "web design": 6, 
            "sql analyst": 6, "junior qa": 6,
            "technical writer": 6,
            
            # Intermediate roles (8-12 weeks)
            "frontend": 10, "front end": 10, "front-end": 10,
            "backend": 10, "back end": 10, "back-end": 10,
            "web developer": 10, "javascript developer": 10,
            "python developer": 10, "java developer": 10,
            "qa engineer": 8, "manual tester": 6,
            "database administrator": 8, "dba": 8,
            "ui designer": 8, "ux designer": 8,
            
            # Advanced roles (12-16 weeks)
            "fullstack": 14, "full stack": 14, "full-stack": 14,
            "devops": 14, "sre": 14, "site reliability": 14,
            "mobile developer": 12, "android": 12, "ios": 12,
            "cloud engineer": 14, "aws": 12, "azure": 12,
            "data analyst": 10, "business analyst": 10,
            "software engineer": 14, "software developer": 12,
            
            # Complex roles (16-24 weeks)
            "data scientist": 18, "data science": 18,
            "machine learning": 20, "ml engineer": 20, "aiml": 20,
            "ai engineer": 22, "artificial intelligence": 22,
            "deep learning": 20, "nlp engineer": 20,
            "cybersecurity": 16, "security engineer": 16,
            "blockchain": 16, "web3": 14,
            "solutions architect": 18, "system architect": 18,
        }
        
        # Find matching role
        base_weeks = 12  # Default
        for key, weeks in role_durations.items():
            if key in role_lower:
                base_weeks = weeks
                break
        
        # Adjust based on experience level
        if profile and profile.experience_level:
            exp_level = profile.experience_level.lower()
            if exp_level == "beginner" or exp_level == "student":
                base_weeks = int(base_weeks * 1.25)  # Add 25% more time for beginners
            elif exp_level == "intermediate":
                base_weeks = int(base_weeks * 1.0)  # Standard time
            elif exp_level == "advanced" or exp_level == "expert":
                base_weeks = int(base_weeks * 0.75)  # 25% less time for experienced
        
        # Cap between 4 and 24 weeks
        return max(4, min(24, base_weeks))
    
    def _define_learning_phases(
        self, 
        target_role: str, 
        duration_weeks: int, 
        skills: List[str],
        experience_level: str
    ) -> List[Dict[str, Any]]:
        """Define structured learning phases based on the role and duration."""
        
        # Distribute skills across phases
        skills_per_phase = max(2, len(skills) // 4) if skills else 2
        
        phases = []
        
        if duration_weeks >= 1:
            phases.append({
                "phase_name": "Foundation",
                "phase_number": 1,
                "start_week": 1,
                "end_week": min(3, duration_weeks),
                "focus": "Environment setup, fundamentals, and basic concepts",
                "skills": skills[:skills_per_phase] if skills else ["Core Fundamentals"],
                "goal": f"Set up your {target_role} development environment and understand core concepts",
                "project_type": "Hello World & Basic Exercises"
            })
        
        if duration_weeks >= 4:
            phases.append({
                "phase_name": "Core Skills",
                "phase_number": 2,
                "start_week": 4,
                "end_week": min(6, duration_weeks),
                "focus": "Deep dive into essential technologies and patterns",
                "skills": skills[skills_per_phase:skills_per_phase*2] if len(skills) > skills_per_phase else skills[:2],
                "goal": f"Master the core technologies required for a {target_role}",
                "project_type": "Mini Projects & Coding Challenges"
            })
        
        if duration_weeks >= 7:
            phases.append({
                "phase_name": "Intermediate",
                "phase_number": 3,
                "start_week": 7,
                "end_week": min(9, duration_weeks),
                "focus": "Advanced concepts, best practices, and real-world patterns",
                "skills": skills[skills_per_phase*2:skills_per_phase*3] if len(skills) > skills_per_phase*2 else skills[2:4],
                "goal": f"Apply advanced techniques used by professional {target_role}s",
                "project_type": "Feature-Complete Project"
            })
        
        if duration_weeks >= 10:
            phases.append({
                "phase_name": "Advanced & Portfolio",
                "phase_number": 4,
                "start_week": 10,
                "end_week": duration_weeks,
                "focus": "Portfolio project, interview prep, and job-ready skills",
                "skills": skills[skills_per_phase*3:] if len(skills) > skills_per_phase*3 else skills[-2:],
                "goal": f"Build a portfolio-worthy project and prepare for {target_role} interviews",
                "project_type": "Full Portfolio Project"
            })
        
        return phases
    
    async def _generate_phase_weeks(
        self,
        target_role: str,
        phase: Dict[str, Any],
        daily_minutes: int,
        experience_level: str,
        learning_style: str,
        all_skills: List[str]
    ) -> Dict[str, Any]:
        """Generate weeks for a specific learning phase using AI with 7 days per week."""
        
        start_week = phase["start_week"]
        end_week = phase["end_week"]
        num_weeks = end_week - start_week + 1
        
        # Get detailed topic breakdown for this phase
        topic_details = self._get_detailed_topics_for_skill(phase["skills"], target_role)
        
        system_prompt = f"""You are a world-class {target_role} educator creating a step-by-step learning curriculum.
Your task is to create SPECIFIC, ACTIONABLE tasks that tell students EXACTLY what to do.
DO NOT use generic phrases like "Learn the basics" or "Study fundamentals".
Instead, be SPECIFIC: "Create a variables.js file and practice declaring let, const, var with 10 examples".
Return ONLY valid JSON - no explanations, no markdown."""

        user_prompt = f"""Create a DETAILED {num_weeks}-week curriculum (Weeks {start_week}-{end_week}) for becoming a **{target_role}**.

## Phase: {phase["phase_name"]}
- **Skills to teach**: {', '.join(phase["skills"])}
- **Topics to cover**: {topic_details}
- **End goal**: {phase["goal"]}

## Student Profile:
- Level: {experience_level}
- Available time: {daily_minutes} minutes/day
- Style: {learning_style}

## CRITICAL REQUIREMENTS:
1. **7 DAYS per week** (Day 1 through Day 7)
2. **1-2 tasks per day** (respect their {daily_minutes} min/day limit)
3. **SPECIFIC task titles** - Tell exactly what to do:
   - ✅ GOOD: "Create a portfolio webpage with HTML: header, nav, main, footer sections"
   - ❌ BAD: "Learn HTML basics"
   - ✅ GOOD: "Build a to-do list app: Add, delete, mark complete functionality"
   - ❌ BAD: "Practice JavaScript"
4. **DETAILED descriptions** with step-by-step instructions:
   - What files to create
   - What code to write
   - What output to expect
   - How to test your work
5. **REAL resource URLs**:
   - MDN: developer.mozilla.org
   - FreeCodeCamp: freecodecamp.org/learn
   - YouTube: specific video titles
   - Practice: codewars.com, leetcode.com

## Weekly Schedule Pattern:
- Days 1-2: Learn new concept (reading/video)
- Days 3-4: Practice exercises (coding)
- Days 5-6: Build mini-project (project)
- Day 7: Review, refactor, and prepare for next week

## JSON Structure:
{{
  "weeks": [
    {{
      "week_number": {start_week},
      "focus_area": "Week {start_week}: [SPECIFIC TOPIC - e.g., 'HTML Structure & Semantic Elements']",
      "learning_objectives": ["Build a complete webpage with 5+ sections", "Use all semantic HTML5 tags correctly"],
      "days": [
        {{
          "day_number": 1,
          "tasks": [
            {{
              "title": "[SPECIFIC ACTION] - e.g., 'Set up VS Code and create your first HTML file with doctype, head, body'",
              "description": "Step 1: Download VS Code from code.visualstudio.com\\nStep 2: Install Live Server extension\\nStep 3: Create a folder 'my-first-website'\\nStep 4: Create index.html with basic structure\\nStep 5: Add a heading and paragraph\\nStep 6: Open with Live Server to see result",
              "task_type": "coding",
              "estimated_duration": {daily_minutes},
              "difficulty": {phase["phase_number"] + 1},
              "learning_objectives": ["Set up development environment", "Create valid HTML5 document structure"],
              "success_criteria": "You have a working index.html that displays in the browser with Live Server",
              "prerequisites": [],
              "resources": [
                {{"title": "VS Code Download", "url": "https://code.visualstudio.com/download", "type": "tool"}},
                {{"title": "MDN HTML Basics", "url": "https://developer.mozilla.org/en-US/docs/Learn/Getting_started_with_the_web/HTML_basics", "type": "documentation"}}
              ]
            }}
          ]
        }}
      ]
    }}
  ],
  "milestones": [
    {{
      "week_number": {end_week},
      "title": "[SPECIFIC ACHIEVEMENT] - e.g., 'Built 3 complete webpages with responsive design'",
      "description": "Completed projects that demonstrate mastery of {', '.join(phase['skills'])}",
      "skills_demonstrated": {phase["skills"]},
      "deliverable": "Working project deployed on GitHub Pages"
    }}
  ]
}}

Generate {num_weeks} weeks with 7 days each. Make every task SPECIFIC and ACTIONABLE for a {target_role}."""

        try:
            logger.info(f"Generating phase {phase['phase_name']} (weeks {start_week}-{end_week}) with 7 days/week...")
            result = await self.llm.generate_json(system_prompt, user_prompt)
            
            if "weeks" in result and result["weeks"]:
                logger.info(f"Successfully generated {len(result['weeks'])} weeks for {phase['phase_name']}")
                return result
            else:
                logger.warning(f"AI response missing weeks for {phase['phase_name']}, using defaults")
                return self._generate_default_phase_weeks(target_role, phase, daily_minutes)
                
        except Exception as e:
            logger.error(f"Error generating phase {phase['phase_name']}: {str(e)}")
            return self._generate_default_phase_weeks(target_role, phase, daily_minutes)
    
    def _get_detailed_topics_for_skill(self, skills: List[str], target_role: str) -> str:
        """Get detailed topic breakdown for skills."""
        topic_map = {
            "HTML": "Document structure, semantic tags (header/nav/main/article/section/footer), forms, tables, accessibility",
            "CSS": "Selectors, box model, flexbox, grid, responsive design, animations, variables, media queries",
            "JavaScript": "Variables, data types, functions, arrays, objects, DOM manipulation, events, async/await, fetch API",
            "React": "Components, JSX, props, state, hooks (useState/useEffect), routing, context, forms",
            "Node.js": "npm, modules, Express.js, middleware, routing, REST APIs, environment variables",
            "Python": "Variables, data types, functions, lists/dicts, file I/O, classes, modules, virtual environments",
            "SQL": "SELECT, INSERT, UPDATE, DELETE, JOINs, GROUP BY, indexes, transactions, normalization",
            "Git": "init, add, commit, push, pull, branches, merge, conflicts, pull requests, .gitignore",
            "Docker": "Images, containers, Dockerfile, docker-compose, volumes, networks, registries",
            "TypeScript": "Types, interfaces, generics, enums, type guards, utility types, configuration",
        }
        
        topics = []
        for skill in skills:
            for key, value in topic_map.items():
                if key.lower() in skill.lower():
                    topics.append(f"{skill}: {value}")
                    break
            else:
                topics.append(f"{skill}: fundamentals, intermediate concepts, practical applications, best practices")
        
        return "; ".join(topics) if topics else f"Core concepts for {target_role}"
    
    def _get_weekly_curriculum(self, target_role: str) -> List[Dict[str, Any]]:
        """Get a detailed week-by-week curriculum for a specific role."""
        role_lower = target_role.lower()
        
        # Full Stack Developer Curriculum (14 weeks)
        fullstack_curriculum = [
            {"week": 1, "topic": "HTML5 Fundamentals", "focus": "Document Structure & Semantic Elements",
             "tasks": [
                 {"day": 1, "title": "Set Up VS Code & Create Your First HTML File", "type": "coding",
                  "desc": "Install VS Code, Live Server extension. Create index.html with doctype, head, body, title. Add h1 and p tags."},
                 {"day": 2, "title": "Learn Semantic HTML Tags: header, nav, main, footer", "type": "reading",
                  "desc": "Read MDN docs on semantic HTML. Create a webpage with proper semantic structure. Understand why semantics matter for SEO."},
                 {"day": 3, "title": "Build a Multi-Section Webpage with article, section, aside", "type": "coding",
                  "desc": "Create a blog-style page with header, navigation, 3 articles, sidebar, and footer. Use proper heading hierarchy."},
                 {"day": 4, "title": "HTML Forms: input, select, textarea, button", "type": "coding",
                  "desc": "Build a contact form with name, email, message, dropdown for topic. Add form validation attributes."},
                 {"day": 5, "title": "Tables & Lists: Create a Pricing Table", "type": "coding",
                  "desc": "Build a pricing comparison table with 3 plans. Use thead, tbody, th, td. Style with basic inline CSS."},
                 {"day": 6, "title": "Project: Build Complete Portfolio HTML Structure", "type": "project",
                  "desc": "Create a full portfolio page with: hero section, about me, skills list, projects grid, contact form, footer."},
                 {"day": 7, "title": "Review: Validate HTML & Fix Accessibility Issues", "type": "reading",
                  "desc": "Use W3C validator. Add alt text to images. Ensure proper heading order. Test with screen reader."},
             ]},
            {"week": 2, "topic": "CSS3 Fundamentals", "focus": "Selectors, Box Model & Basic Styling",
             "tasks": [
                 {"day": 1, "title": "CSS Selectors: element, class, ID, attribute selectors", "type": "reading",
                  "desc": "Learn selector specificity. Practice with 10 different selector types. Create a cheat sheet."},
                 {"day": 2, "title": "Box Model Deep Dive: margin, padding, border, width", "type": "coding",
                  "desc": "Create colored boxes showing margin vs padding. Understand box-sizing: border-box."},
                 {"day": 3, "title": "Typography & Colors: fonts, colors, text properties", "type": "coding",
                  "desc": "Style a blog post with custom fonts (Google Fonts), color palette, line-height, letter-spacing."},
                 {"day": 4, "title": "Backgrounds & Borders: gradients, images, rounded corners", "type": "coding",
                  "desc": "Create cards with gradient backgrounds, border-radius, box-shadow. Add background images."},
                 {"day": 5, "title": "CSS Units: px, em, rem, %, vh, vw", "type": "coding",
                  "desc": "Build a page using only relative units. Understand when to use each unit type."},
                 {"day": 6, "title": "Project: Style Your Portfolio Page with CSS", "type": "project",
                  "desc": "Apply styles to Week 1 portfolio: color scheme, typography, spacing, borders, shadows."},
                 {"day": 7, "title": "Review: CSS Organization & Best Practices", "type": "reading",
                  "desc": "Learn BEM naming convention. Organize CSS into sections. Create reusable utility classes."},
             ]},
            {"week": 3, "topic": "CSS Flexbox & Grid", "focus": "Modern Layout Techniques",
             "tasks": [
                 {"day": 1, "title": "Flexbox Container: display flex, justify-content, align-items", "type": "reading",
                  "desc": "Read CSS Tricks Flexbox guide. Build a navbar with evenly spaced links using flex."},
                 {"day": 2, "title": "Flexbox Items: flex-grow, flex-shrink, flex-basis, order", "type": "coding",
                  "desc": "Create a card layout where cards grow/shrink. Build a holy grail layout."},
                 {"day": 3, "title": "CSS Grid Basics: grid-template-columns, rows, gap", "type": "reading",
                  "desc": "Read CSS Tricks Grid guide. Create a 12-column grid system from scratch."},
                 {"day": 4, "title": "Grid Areas & Placement: grid-area, grid-template-areas", "type": "coding",
                  "desc": "Build a magazine-style layout using named grid areas. Create asymmetric designs."},
                 {"day": 5, "title": "Responsive Design: media queries, mobile-first approach", "type": "coding",
                  "desc": "Make your grid layout responsive. Create breakpoints for mobile, tablet, desktop."},
                 {"day": 6, "title": "Project: Responsive Portfolio with Flexbox & Grid", "type": "project",
                  "desc": "Rebuild portfolio layout using Flexbox for navbar, Grid for projects. Make fully responsive."},
                 {"day": 7, "title": "Review: Flexbox vs Grid - When to Use Which", "type": "reading",
                  "desc": "Document use cases for each. Practice with Flexbox Froggy and Grid Garden games."},
             ]},
            {"week": 4, "topic": "JavaScript Basics", "focus": "Variables, Data Types & Operators",
             "tasks": [
                 {"day": 1, "title": "Variables: let, const, var - Differences & Best Practices", "type": "reading",
                  "desc": "Understand hoisting, scope, temporal dead zone. Write 10 examples showing when to use each."},
                 {"day": 2, "title": "Data Types: strings, numbers, booleans, null, undefined", "type": "coding",
                  "desc": "Practice type coercion, typeof operator. Build a type checker function."},
                 {"day": 3, "title": "Operators: arithmetic, comparison, logical, ternary", "type": "coding",
                  "desc": "Solve 15 exercises using different operators. Build a simple calculator."},
                 {"day": 4, "title": "Control Flow: if/else, switch, loops (for, while)", "type": "coding",
                  "desc": "Write FizzBuzz, find prime numbers, reverse a string using loops."},
                 {"day": 5, "title": "Functions: declaration, expression, arrow functions", "type": "coding",
                  "desc": "Create 10 utility functions. Understand this context in different function types."},
                 {"day": 6, "title": "Project: Interactive Quiz App (Console)", "type": "project",
                  "desc": "Build a quiz game that runs in console. Track score, show results, handle edge cases."},
                 {"day": 7, "title": "Review: Debug JavaScript & Use DevTools Console", "type": "reading",
                  "desc": "Learn console.log, debugger, breakpoints. Fix 5 buggy code snippets."},
             ]},
            {"week": 5, "topic": "JavaScript Arrays & Objects", "focus": "Data Structures & Methods",
             "tasks": [
                 {"day": 1, "title": "Arrays: Creating, Accessing, Modifying Elements", "type": "reading",
                  "desc": "Learn array methods: push, pop, shift, unshift, splice, slice. Practice with 10 exercises."},
                 {"day": 2, "title": "Array Iteration: forEach, map, filter, reduce", "type": "coding",
                  "desc": "Transform data using these methods. No for loops allowed challenge."},
                 {"day": 3, "title": "Objects: Creating, Accessing, Nested Objects", "type": "coding",
                  "desc": "Build a user profile object. Practice dot notation vs bracket notation."},
                 {"day": 4, "title": "Object Methods: keys, values, entries, assign, spread", "type": "coding",
                  "desc": "Merge objects, clone objects, destructuring. Build a settings manager."},
                 {"day": 5, "title": "JSON: Parse, Stringify, Working with API Data", "type": "coding",
                  "desc": "Convert between JSON and objects. Practice with mock API responses."},
                 {"day": 6, "title": "Project: Todo List Data Management (No UI Yet)", "type": "project",
                  "desc": "Create todo CRUD operations using arrays/objects. Add, remove, update, filter todos."},
                 {"day": 7, "title": "Review: Array/Object Practice Problems", "type": "coding",
                  "desc": "Solve 5 LeetCode easy problems involving arrays and objects."},
             ]},
            {"week": 6, "topic": "DOM Manipulation", "focus": "Connecting JavaScript to HTML",
             "tasks": [
                 {"day": 1, "title": "Selecting Elements: getElementById, querySelector, querySelectorAll", "type": "reading",
                  "desc": "Practice selecting elements in different ways. Understand NodeList vs HTMLCollection."},
                 {"day": 2, "title": "Modifying Elements: textContent, innerHTML, attributes, classList", "type": "coding",
                  "desc": "Build a profile card that updates dynamically. Toggle classes for themes."},
                 {"day": 3, "title": "Creating Elements: createElement, appendChild, insertBefore", "type": "coding",
                  "desc": "Build a list that adds items dynamically. Create elements from array data."},
                 {"day": 4, "title": "Event Handling: click, submit, input, keypress events", "type": "coding",
                  "desc": "Build a form that validates on input. Create keyboard shortcuts."},
                 {"day": 5, "title": "Event Delegation & Bubbling", "type": "coding",
                  "desc": "Handle events on dynamic elements. Build a task list with event delegation."},
                 {"day": 6, "title": "Project: Interactive Todo App with Full UI", "type": "project",
                  "desc": "Combine Week 5 logic with DOM. Add todos, mark complete, delete, filter by status."},
                 {"day": 7, "title": "Review: DOM Performance & Best Practices", "type": "reading",
                  "desc": "Learn about reflows, batch DOM updates, documentFragment. Optimize your todo app."},
             ]},
            {"week": 7, "topic": "Async JavaScript", "focus": "Promises, Async/Await & Fetch API",
             "tasks": [
                 {"day": 1, "title": "Understanding Asynchronous JavaScript & Callbacks", "type": "reading",
                  "desc": "Learn event loop, call stack, callback queue. Understand callback hell."},
                 {"day": 2, "title": "Promises: Creating, Chaining, Error Handling", "type": "coding",
                  "desc": "Convert callback code to promises. Practice .then(), .catch(), .finally()."},
                 {"day": 3, "title": "Async/Await: Cleaner Async Code", "type": "coding",
                  "desc": "Refactor promises to async/await. Handle errors with try/catch."},
                 {"day": 4, "title": "Fetch API: GET Requests to Public APIs", "type": "coding",
                  "desc": "Fetch data from JSONPlaceholder API. Display posts, users, comments."},
                 {"day": 5, "title": "Fetch API: POST, PUT, DELETE Requests", "type": "coding",
                  "desc": "Create, update, delete data via API. Build a CRUD interface."},
                 {"day": 6, "title": "Project: Weather App with Real API", "type": "project",
                  "desc": "Use OpenWeatherMap API. Search city, display weather, handle loading/errors."},
                 {"day": 7, "title": "Review: Error Handling & Loading States", "type": "reading",
                  "desc": "Add proper error messages, loading spinners, retry logic to weather app."},
             ]},
            {"week": 8, "topic": "React Fundamentals", "focus": "Components, JSX & Props",
             "tasks": [
                 {"day": 1, "title": "Set Up React with Vite: Create Your First Component", "type": "coding",
                  "desc": "Install Node.js, create Vite React app. Understand project structure. Create App component."},
                 {"day": 2, "title": "JSX Deep Dive: Expressions, Conditionals, Lists", "type": "reading",
                  "desc": "Learn JSX syntax, embed expressions, conditional rendering, map through arrays."},
                 {"day": 3, "title": "Components: Function Components & Component Composition", "type": "coding",
                  "desc": "Create Header, Footer, Card components. Compose them together."},
                 {"day": 4, "title": "Props: Passing Data Between Components", "type": "coding",
                  "desc": "Pass props to Card component. Use destructuring, default props, prop types."},
                 {"day": 5, "title": "Styling in React: CSS Modules, Inline Styles, Tailwind", "type": "coding",
                  "desc": "Try different styling approaches. Set up Tailwind CSS in your project."},
                 {"day": 6, "title": "Project: Static Portfolio in React", "type": "project",
                  "desc": "Convert HTML portfolio to React. Create reusable components for each section."},
                 {"day": 7, "title": "Review: React DevTools & Component Best Practices", "type": "reading",
                  "desc": "Install React DevTools. Learn component naming, file organization."},
             ]},
            {"week": 9, "topic": "React State & Hooks", "focus": "useState, useEffect & Events",
             "tasks": [
                 {"day": 1, "title": "useState Hook: Managing Component State", "type": "reading",
                  "desc": "Understand state vs props. Create counter, toggle, form state examples."},
                 {"day": 2, "title": "Handling Events in React: onClick, onChange, onSubmit", "type": "coding",
                  "desc": "Build a form with controlled inputs. Handle button clicks, form submissions."},
                 {"day": 3, "title": "useEffect Hook: Side Effects & Lifecycle", "type": "coding",
                  "desc": "Fetch data on mount, update document title, set up intervals. Clean up effects."},
                 {"day": 4, "title": "Lifting State Up: Sharing State Between Components", "type": "coding",
                  "desc": "Build a parent-child component pair that shares state. Temperature converter."},
                 {"day": 5, "title": "Forms in React: Controlled Components & Validation", "type": "coding",
                  "desc": "Build a signup form with validation. Show errors, disable submit until valid."},
                 {"day": 6, "title": "Project: Todo App in React", "type": "project",
                  "desc": "Rebuild todo app in React. Add/remove/toggle todos. Filter by status. Persist to localStorage."},
                 {"day": 7, "title": "Review: Common useState/useEffect Mistakes", "type": "reading",
                  "desc": "Learn about stale closures, missing dependencies, infinite loops. Fix buggy examples."},
             ]},
            {"week": 10, "topic": "Node.js & Express Basics", "focus": "Backend Development Introduction",
             "tasks": [
                 {"day": 1, "title": "Node.js Setup: npm, package.json, modules", "type": "reading",
                  "desc": "Install Node.js, understand npm, create package.json. Use require/import."},
                 {"day": 2, "title": "Express.js: Create Your First Server", "type": "coding",
                  "desc": "Install Express, create server, handle GET request, send JSON response."},
                 {"day": 3, "title": "Express Routing: params, query, body", "type": "coding",
                  "desc": "Create routes for /users, /users/:id. Handle query params, request body."},
                 {"day": 4, "title": "Middleware: Built-in, Custom, Error Handling", "type": "coding",
                  "desc": "Use express.json(), create logging middleware, handle errors globally."},
                 {"day": 5, "title": "REST API Design: CRUD Operations", "type": "coding",
                  "desc": "Build full CRUD API for a resource. Follow REST conventions."},
                 {"day": 6, "title": "Project: Build a Todo REST API", "type": "project",
                  "desc": "Create API with GET/POST/PUT/DELETE for todos. Store in memory array."},
                 {"day": 7, "title": "Review: API Testing with Postman/Thunder Client", "type": "reading",
                  "desc": "Install Postman or Thunder Client. Test all API endpoints. Create collection."},
             ]},
            {"week": 11, "topic": "Database with PostgreSQL", "focus": "SQL & Database Integration",
             "tasks": [
                 {"day": 1, "title": "SQL Basics: SELECT, INSERT, UPDATE, DELETE", "type": "reading",
                  "desc": "Set up PostgreSQL, use psql or pgAdmin. Practice basic CRUD queries."},
                 {"day": 2, "title": "SQL Joins: INNER, LEFT, RIGHT, relationships", "type": "coding",
                  "desc": "Create users and posts tables. Write queries with JOINs."},
                 {"day": 3, "title": "Connect Node.js to PostgreSQL with pg", "type": "coding",
                  "desc": "Install pg package. Create connection pool. Execute queries from Node."},
                 {"day": 4, "title": "CRUD API with Database: Replace in-memory with SQL", "type": "coding",
                  "desc": "Update todo API to use PostgreSQL. Handle async/await with queries."},
                 {"day": 5, "title": "Database Migrations & Schema Design", "type": "coding",
                  "desc": "Plan database schema. Create migration files. Set up proper data types."},
                 {"day": 6, "title": "Project: Full Stack Todo with Database", "type": "project",
                  "desc": "Connect React frontend to Express API to PostgreSQL. Full CRUD working."},
                 {"day": 7, "title": "Review: SQL Injection & Prepared Statements", "type": "reading",
                  "desc": "Learn about SQL injection. Use parameterized queries. Security best practices."},
             ]},
            {"week": 12, "topic": "Authentication & Authorization", "focus": "User Login System",
             "tasks": [
                 {"day": 1, "title": "Password Hashing: bcrypt for secure storage", "type": "reading",
                  "desc": "Never store plain passwords. Use bcrypt to hash. Compare hashed passwords."},
                 {"day": 2, "title": "User Registration: Sign up endpoint", "type": "coding",
                  "desc": "Create /auth/register endpoint. Validate input, hash password, store user."},
                 {"day": 3, "title": "JWT Authentication: Login & Token Generation", "type": "coding",
                  "desc": "Create /auth/login endpoint. Generate JWT on successful login."},
                 {"day": 4, "title": "Protected Routes: Auth Middleware", "type": "coding",
                  "desc": "Create middleware to verify JWT. Protect todo routes. Get user from token."},
                 {"day": 5, "title": "React Auth: Login Form & Token Storage", "type": "coding",
                  "desc": "Create login page in React. Store token in localStorage. Add to API requests."},
                 {"day": 6, "title": "Project: Complete Auth System", "type": "project",
                  "desc": "Register, login, protected dashboard, logout. Show user-specific todos only."},
                 {"day": 7, "title": "Review: Security Best Practices", "type": "reading",
                  "desc": "Learn about CORS, HTTPS, token expiration, refresh tokens."},
             ]},
            {"week": 13, "topic": "Deployment & DevOps Basics", "focus": "Going Live",
             "tasks": [
                 {"day": 1, "title": "Git & GitHub: Version Control Setup", "type": "reading",
                  "desc": "Initialize git repo, create .gitignore, push to GitHub. Write good commit messages."},
                 {"day": 2, "title": "Environment Variables: Managing Secrets", "type": "coding",
                  "desc": "Use dotenv, create .env files for dev/prod. Never commit secrets."},
                 {"day": 3, "title": "Deploy Frontend: Vercel or Netlify", "type": "coding",
                  "desc": "Deploy React app to Vercel. Set up custom domain, environment variables."},
                 {"day": 4, "title": "Deploy Backend: Railway or Render", "type": "coding",
                  "desc": "Deploy Express API to Railway. Connect to cloud PostgreSQL."},
                 {"day": 5, "title": "CI/CD: Automatic Deployments", "type": "coding",
                  "desc": "Set up auto-deploy on push to main branch. Test deployment pipeline."},
                 {"day": 6, "title": "Project: Deploy Full Stack App", "type": "project",
                  "desc": "Both frontend and backend live. Connected to production database. Working auth."},
                 {"day": 7, "title": "Review: Monitoring & Debugging Production", "type": "reading",
                  "desc": "Set up error logging, check deployment logs, handle production issues."},
             ]},
            {"week": 14, "topic": "Portfolio & Job Prep", "focus": "Getting Hired",
             "tasks": [
                 {"day": 1, "title": "Polish Portfolio: Add All Projects", "type": "project",
                  "desc": "Update portfolio with todo app, weather app. Add descriptions, screenshots, links."},
                 {"day": 2, "title": "GitHub Profile: README & Contribution Graph", "type": "coding",
                  "desc": "Create profile README. Pin best repos. Write good project descriptions."},
                 {"day": 3, "title": "LinkedIn: Technical Profile Setup", "type": "reading",
                  "desc": "Update headline, about section, add projects. Connect with developers."},
                 {"day": 4, "title": "Resume: Technical Resume Writing", "type": "project",
                  "desc": "Create ATS-friendly resume. Focus on projects, skills, impact."},
                 {"day": 5, "title": "Practice: Common Interview Questions", "type": "reading",
                  "desc": "Review HTML/CSS/JS/React fundamentals. Practice explaining your projects."},
                 {"day": 6, "title": "Coding Challenge: Solve 5 Easy LeetCode Problems", "type": "coding",
                  "desc": "Practice array, string, object problems. Focus on clean solutions."},
                 {"day": 7, "title": "Final Review: Celebrate Your Journey!", "type": "reading",
                  "desc": "Review everything learned. Plan next steps. Start applying!"},
             ]},
        ]
        
        # Other role curriculums can be added similarly
        curriculums = {
            "fullstack": fullstack_curriculum,
            "full stack": fullstack_curriculum,
            "full-stack": fullstack_curriculum,
            "web developer": fullstack_curriculum[:10],  # First 10 weeks
            "frontend": fullstack_curriculum[:8],  # First 8 weeks (HTML/CSS/JS/React)
            "front end": fullstack_curriculum[:8],
        }
        
        # Find matching curriculum
        for key, curriculum in curriculums.items():
            if key in role_lower:
                return curriculum
        
        # Return None if no specific curriculum exists
        return None
    
    def _generate_default_phase_weeks(
        self,
        target_role: str,
        phase: Dict[str, Any],
        daily_minutes: int
    ) -> Dict[str, Any]:
        """Generate default weeks for a phase - uses detailed curriculum if available."""
        
        # Try to get pre-defined curriculum
        curriculum = self._get_weekly_curriculum(target_role)
        
        if curriculum:
            # Use the detailed curriculum
            weeks = []
            for week_num in range(phase["start_week"], phase["end_week"] + 1):
                if week_num <= len(curriculum):
                    week_data = curriculum[week_num - 1]
                    days = []
                    for task_data in week_data["tasks"]:
                        days.append({
                            "day_number": task_data["day"],
                            "tasks": [{
                                "title": task_data["title"],
                                "description": task_data["desc"],
                                "task_type": task_data["type"],
                                "estimated_duration": daily_minutes,
                                "difficulty": phase["phase_number"] + 1,
                                "learning_objectives": [f"Complete: {task_data['title']}"],
                                "success_criteria": f"Successfully completed the task",
                                "prerequisites": [],
                                "resources": self._get_resources_for_topic(week_data["topic"])
                            }]
                        })
                    weeks.append({
                        "week_number": week_num,
                        "focus_area": f"Week {week_num}: {week_data['topic']} - {week_data['focus']}",
                        "learning_objectives": [week_data["focus"]],
                        "days": days
                    })
                else:
                    # Generate generic week if curriculum doesn't cover this week
                    weeks.append(self._generate_generic_week(target_role, week_num, phase, daily_minutes))
            
            return {
                "weeks": weeks,
                "milestones": [{
                    "week_number": phase["end_week"],
                    "title": f"{phase['phase_name']} Complete",
                    "description": f"Completed weeks {phase['start_week']}-{phase['end_week']}",
                    "skills_demonstrated": phase.get("skills", []),
                    "deliverable": "Working projects pushed to GitHub"
                }]
            }
        
        # Fallback to generic generation
        return self._generate_generic_phase_weeks(target_role, phase, daily_minutes)
    
    def _get_resources_for_topic(self, topic: str) -> List[Dict[str, str]]:
        """Get relevant resources for a topic - COMPREHENSIVE RESOURCE DATABASE."""
        topic_lower = topic.lower()
        
        if "html" in topic_lower:
            return [
                {"title": "MDN HTML Guide", "url": "https://developer.mozilla.org/en-US/docs/Learn/HTML", "type": "documentation"},
                {"title": "freeCodeCamp HTML", "url": "https://www.freecodecamp.org/learn/2022/responsive-web-design/", "type": "tutorial"}
            ]
        elif "css" in topic_lower:
            return [
                {"title": "MDN CSS Guide", "url": "https://developer.mozilla.org/en-US/docs/Learn/CSS", "type": "documentation"},
                {"title": "CSS Tricks", "url": "https://css-tricks.com/", "type": "tutorial"}
            ]
        elif "javascript" in topic_lower or "js" in topic_lower:
            return [
                {"title": "JavaScript.info", "url": "https://javascript.info/", "type": "documentation"},
                {"title": "freeCodeCamp JS", "url": "https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/", "type": "tutorial"}
            ]
        elif "react" in topic_lower:
            return [
                {"title": "React Official Docs", "url": "https://react.dev/learn", "type": "documentation"},
                {"title": "React Tutorial", "url": "https://react.dev/learn/tutorial-tic-tac-toe", "type": "tutorial"}
            ]
        elif "node" in topic_lower or "express" in topic_lower:
            return [
                {"title": "Node.js Docs", "url": "https://nodejs.org/en/docs/", "type": "documentation"},
                {"title": "Express Guide", "url": "https://expressjs.com/en/starter/installing.html", "type": "tutorial"}
            ]
        elif "sql" in topic_lower or "postgres" in topic_lower or "database" in topic_lower:
            return [
                {"title": "PostgreSQL Tutorial", "url": "https://www.postgresqltutorial.com/", "type": "documentation"},
                {"title": "SQL Practice", "url": "https://sqlbolt.com/", "type": "tutorial"}
            ]
        elif "python" in topic_lower:
            return [
                {"title": "Python Official Tutorial", "url": "https://docs.python.org/3/tutorial/", "type": "documentation"},
                {"title": "Real Python", "url": "https://realpython.com/", "type": "tutorial"}
            ]
        elif "machine learning" in topic_lower or "ml" in topic_lower:
            return [
                {"title": "Scikit-learn Tutorial", "url": "https://scikit-learn.org/stable/tutorial/", "type": "documentation"},
                {"title": "Kaggle Learn ML", "url": "https://www.kaggle.com/learn/intro-to-machine-learning", "type": "tutorial"}
            ]
        elif "deep learning" in topic_lower or "neural" in topic_lower:
            return [
                {"title": "Deep Learning Book", "url": "https://www.deeplearningbook.org/", "type": "documentation"},
                {"title": "Fast.ai Course", "url": "https://course.fast.ai/", "type": "tutorial"}
            ]
        elif "tensorflow" in topic_lower or "keras" in topic_lower:
            return [
                {"title": "TensorFlow Tutorials", "url": "https://www.tensorflow.org/tutorials", "type": "documentation"},
                {"title": "Keras Guide", "url": "https://keras.io/guides/", "type": "tutorial"}
            ]
        elif "pytorch" in topic_lower:
            return [
                {"title": "PyTorch Tutorials", "url": "https://pytorch.org/tutorials/", "type": "documentation"},
                {"title": "PyTorch Examples", "url": "https://github.com/pytorch/examples", "type": "tutorial"}
            ]
        elif "nlp" in topic_lower or "natural language" in topic_lower:
            return [
                {"title": "Hugging Face Course", "url": "https://huggingface.co/course/", "type": "documentation"},
                {"title": "spaCy Course", "url": "https://course.spacy.io/", "type": "tutorial"}
            ]
        elif "pandas" in topic_lower:
            return [
                {"title": "Pandas Documentation", "url": "https://pandas.pydata.org/docs/getting_started/", "type": "documentation"},
                {"title": "Kaggle Pandas", "url": "https://www.kaggle.com/learn/pandas", "type": "tutorial"}
            ]
        elif "numpy" in topic_lower:
            return [
                {"title": "NumPy Quickstart", "url": "https://numpy.org/doc/stable/user/quickstart.html", "type": "documentation"},
                {"title": "NumPy Tutorial", "url": "https://www.w3schools.com/python/numpy/", "type": "tutorial"}
            ]
        elif "visualization" in topic_lower or "matplotlib" in topic_lower or "seaborn" in topic_lower:
            return [
                {"title": "Matplotlib Tutorials", "url": "https://matplotlib.org/stable/tutorials/", "type": "documentation"},
                {"title": "Seaborn Tutorial", "url": "https://seaborn.pydata.org/tutorial.html", "type": "tutorial"}
            ]
        elif "docker" in topic_lower:
            return [
                {"title": "Docker Get Started", "url": "https://docs.docker.com/get-started/", "type": "documentation"},
                {"title": "Docker Tutorial", "url": "https://docker-curriculum.com/", "type": "tutorial"}
            ]
        elif "kubernetes" in topic_lower or "k8s" in topic_lower:
            return [
                {"title": "Kubernetes Docs", "url": "https://kubernetes.io/docs/tutorials/", "type": "documentation"},
                {"title": "K8s the Hard Way", "url": "https://github.com/kelseyhightower/kubernetes-the-hard-way", "type": "tutorial"}
            ]
        elif "aws" in topic_lower:
            return [
                {"title": "AWS Documentation", "url": "https://docs.aws.amazon.com/", "type": "documentation"},
                {"title": "AWS Skill Builder", "url": "https://explore.skillbuilder.aws/", "type": "tutorial"}
            ]
        elif "git" in topic_lower:
            return [
                {"title": "Pro Git Book", "url": "https://git-scm.com/book/", "type": "documentation"},
                {"title": "Learn Git Branching", "url": "https://learngitbranching.js.org/", "type": "tutorial"}
            ]
        elif "java" in topic_lower:
            return [
                {"title": "Java Tutorial", "url": "https://docs.oracle.com/javase/tutorial/", "type": "documentation"},
                {"title": "Baeldung Java", "url": "https://www.baeldung.com/", "type": "tutorial"}
            ]
        elif "django" in topic_lower:
            return [
                {"title": "Django Documentation", "url": "https://docs.djangoproject.com/", "type": "documentation"},
                {"title": "Django Girls Tutorial", "url": "https://tutorial.djangogirls.org/", "type": "tutorial"}
            ]
        elif "flask" in topic_lower:
            return [
                {"title": "Flask Documentation", "url": "https://flask.palletsprojects.com/", "type": "documentation"},
                {"title": "Flask Mega-Tutorial", "url": "https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world", "type": "tutorial"}
            ]
        else:
            return [
                {"title": "Google Search", "url": f"https://www.google.com/search?q={topic.replace(' ', '+')}+tutorial", "type": "documentation"},
                {"title": "YouTube Tutorials", "url": f"https://www.youtube.com/results?search_query={topic.replace(' ', '+')}+tutorial", "type": "tutorial"}
            ]
    
    def _get_skill_curriculum(self, skill_name: str) -> List[Dict[str, Any]]:
        """
        Get a detailed week-by-week curriculum for ANY skill.
        Each skill has multiple weeks of progressive content.
        This is the DYNAMIC engine that powers all roadmaps.
        """
        skill_lower = skill_name.lower()
        
        # ============== PROGRAMMING LANGUAGES ==============
        if "python" in skill_lower:
            return [
                {"week_topic": "Python Basics: Variables, Data Types & Operators",
                 "tasks": [
                     {"day": 1, "title": "Install Python & Set Up VS Code with Python Extension", "type": "coding", "desc": "Download Python 3.11+, install VS Code, add Python extension. Create hello.py and run it."},
                     {"day": 2, "title": "Variables & Data Types: int, float, str, bool", "type": "reading", "desc": "Learn variable naming, type(), type conversion. Practice with 15 variable examples."},
                     {"day": 3, "title": "Operators: Arithmetic, Comparison, Logical", "type": "coding", "desc": "Build a calculator. Practice ==, !=, and, or, not operators with 10 exercises."},
                     {"day": 4, "title": "Strings: Slicing, Methods, f-strings", "type": "coding", "desc": "Practice string methods: upper(), split(), join(), replace(). Build a text formatter."},
                     {"day": 5, "title": "Input/Output & Control Flow: if/elif/else", "type": "coding", "desc": "Build a grade calculator with user input. Handle edge cases."},
                     {"day": 6, "title": "Project: Build a Number Guessing Game", "type": "project", "desc": "Random number 1-100, user guesses, give hints (higher/lower), count attempts."},
                     {"day": 7, "title": "Review & Debug: Fix 5 Buggy Python Scripts", "type": "reading", "desc": "Practice debugging with print(), learn common errors (IndentationError, TypeError)."},
                 ]},
                {"week_topic": "Python Data Structures: Lists, Tuples, Dictionaries",
                 "tasks": [
                     {"day": 1, "title": "Lists: Creating, Indexing, Slicing", "type": "reading", "desc": "Learn list operations: append, insert, remove, pop. Practice with 10 exercises."},
                     {"day": 2, "title": "List Methods & Comprehensions", "type": "coding", "desc": "Master list comprehensions. Transform data: [x*2 for x in range(10) if x%2==0]."},
                     {"day": 3, "title": "Tuples & Sets: Immutable Data", "type": "coding", "desc": "Understand when to use tuples vs lists. Practice set operations: union, intersection."},
                     {"day": 4, "title": "Dictionaries: Key-Value Storage", "type": "coding", "desc": "Build a contact book with dict. Practice get(), keys(), values(), items()."},
                     {"day": 5, "title": "Nested Data Structures & JSON", "type": "coding", "desc": "Work with nested dicts/lists. Parse JSON data, create data structures."},
                     {"day": 6, "title": "Project: Build a Todo List Manager (CLI)", "type": "project", "desc": "Add, remove, list, mark complete tasks. Store in dict, save to JSON file."},
                     {"day": 7, "title": "Review: Solve 5 LeetCode Easy Problems", "type": "coding", "desc": "Practice Two Sum, Valid Parentheses, Merge Sorted Array."},
                 ]},
                {"week_topic": "Python Functions & Modules",
                 "tasks": [
                     {"day": 1, "title": "Functions: def, Parameters, Return Values", "type": "reading", "desc": "Create functions with positional and keyword arguments. Understand scope."},
                     {"day": 2, "title": "Advanced Functions: *args, **kwargs, Lambda", "type": "coding", "desc": "Build flexible functions. Use lambda with map(), filter(), sorted()."},
                     {"day": 3, "title": "Modules & Packages: import, from, pip", "type": "coding", "desc": "Create your own module. Install packages with pip. Use requirements.txt."},
                     {"day": 4, "title": "File Handling: read, write, with statement", "type": "coding", "desc": "Read/write text and CSV files. Handle exceptions with try/except."},
                     {"day": 5, "title": "Error Handling & Exceptions", "type": "coding", "desc": "Raise custom exceptions. Build robust code with proper error handling."},
                     {"day": 6, "title": "Project: Build a File Organizer Script", "type": "project", "desc": "Organize files by extension into folders. Handle duplicates, log actions."},
                     {"day": 7, "title": "Review: Code Review Best Practices", "type": "reading", "desc": "Learn PEP 8 style guide. Refactor your code for readability."},
                 ]},
                {"week_topic": "Python OOP: Classes & Objects",
                 "tasks": [
                     {"day": 1, "title": "Classes & Objects: __init__, self, attributes", "type": "reading", "desc": "Create a Person class with name, age. Understand self and instance variables."},
                     {"day": 2, "title": "Methods: Instance, Class, Static Methods", "type": "coding", "desc": "Add methods to classes. Use @classmethod and @staticmethod decorators."},
                     {"day": 3, "title": "Inheritance & Polymorphism", "type": "coding", "desc": "Create parent/child classes. Override methods, use super()."},
                     {"day": 4, "title": "Encapsulation & Properties", "type": "coding", "desc": "Use private attributes (_var). Create getters/setters with @property."},
                     {"day": 5, "title": "Magic Methods: __str__, __repr__, __eq__", "type": "coding", "desc": "Customize object behavior. Implement comparison and string methods."},
                     {"day": 6, "title": "Project: Build a Bank Account System", "type": "project", "desc": "Account class with deposit, withdraw, transfer. Handle overdraft, transaction history."},
                     {"day": 7, "title": "Review: Design Patterns Introduction", "type": "reading", "desc": "Learn Singleton, Factory patterns. When to use OOP vs functional."},
                 ]},
            ]
        
        elif "java" in skill_lower and "javascript" not in skill_lower:
            return [
                {"week_topic": "Java Fundamentals: Syntax & Data Types",
                 "tasks": [
                     {"day": 1, "title": "Install JDK & Set Up IntelliJ IDEA", "type": "coding", "desc": "Download JDK 17+, install IntelliJ. Create HelloWorld.java, compile and run."},
                     {"day": 2, "title": "Variables & Primitive Types: int, double, boolean, char", "type": "reading", "desc": "Understand type declarations, type casting. Practice with 15 examples."},
                     {"day": 3, "title": "Operators & Control Flow: if/else, switch", "type": "coding", "desc": "Build a grade calculator. Practice ternary operator and switch statements."},
                     {"day": 4, "title": "Loops: for, while, do-while, enhanced for", "type": "coding", "desc": "Write FizzBuzz, find primes. Practice break, continue statements."},
                     {"day": 5, "title": "Arrays: Declaration, Initialization, Iteration", "type": "coding", "desc": "Work with 1D and 2D arrays. Sort, search, and manipulate arrays."},
                     {"day": 6, "title": "Project: Build a Console-Based Calculator", "type": "project", "desc": "Handle +, -, *, /, %. Use Scanner for input, handle division by zero."},
                     {"day": 7, "title": "Review: Java Naming Conventions & Best Practices", "type": "reading", "desc": "Learn camelCase, PascalCase. Understand Java coding standards."},
                 ]},
                {"week_topic": "Java OOP: Classes, Objects & Methods",
                 "tasks": [
                     {"day": 1, "title": "Classes & Objects: Constructor, this keyword", "type": "reading", "desc": "Create Student class with constructor. Understand this reference."},
                     {"day": 2, "title": "Methods: Parameters, Return Types, Overloading", "type": "coding", "desc": "Create methods with different signatures. Practice method overloading."},
                     {"day": 3, "title": "Access Modifiers: public, private, protected", "type": "coding", "desc": "Implement encapsulation. Create getters/setters for private fields."},
                     {"day": 4, "title": "Inheritance: extends, super, Override", "type": "coding", "desc": "Create class hierarchy. Override methods, call parent constructors."},
                     {"day": 5, "title": "Interfaces & Abstract Classes", "type": "coding", "desc": "Define contracts with interfaces. Implement multiple interfaces."},
                     {"day": 6, "title": "Project: Build an Employee Management System", "type": "project", "desc": "Employee, Manager, Developer classes. Calculate salaries, manage departments."},
                     {"day": 7, "title": "Review: SOLID Principles Introduction", "type": "reading", "desc": "Learn Single Responsibility, Open/Closed principles."},
                 ]},
            ]
        
        elif "javascript" in skill_lower or "js" in skill_lower:
            return [
                {"week_topic": "JavaScript Basics: Variables, Types & Operators",
                 "tasks": [
                     {"day": 1, "title": "Set Up Dev Environment: VS Code, Node.js, Browser Console", "type": "coding", "desc": "Install Node.js, VS Code. Run JS in browser console and with node command."},
                     {"day": 2, "title": "Variables: let, const, var - Differences & Best Practices", "type": "reading", "desc": "Understand hoisting, scope, temporal dead zone. Write 10 examples."},
                     {"day": 3, "title": "Data Types: string, number, boolean, null, undefined, object", "type": "coding", "desc": "Practice typeof, type coercion. Understand truthy/falsy values."},
                     {"day": 4, "title": "Operators: Arithmetic, Comparison (== vs ===), Logical", "type": "coding", "desc": "Build a tip calculator. Understand strict equality vs loose equality."},
                     {"day": 5, "title": "Control Flow: if/else, switch, ternary operator", "type": "coding", "desc": "Build a weather advice app based on temperature input."},
                     {"day": 6, "title": "Project: Build an Interactive Quiz (Console)", "type": "project", "desc": "5 questions, track score, show results. Use prompt() for input."},
                     {"day": 7, "title": "Review: Debug JavaScript with Chrome DevTools", "type": "reading", "desc": "Learn console.log, debugger, breakpoints. Fix 5 buggy scripts."},
                 ]},
                {"week_topic": "JavaScript Functions & Arrays",
                 "tasks": [
                     {"day": 1, "title": "Functions: Declaration, Expression, Arrow Functions", "type": "reading", "desc": "Understand this context differences. Practice with 10 function examples."},
                     {"day": 2, "title": "Arrays: Creating, Accessing, Modifying", "type": "coding", "desc": "Practice push, pop, shift, unshift, splice, slice. Build a playlist manager."},
                     {"day": 3, "title": "Array Methods: map, filter, reduce, find, forEach", "type": "coding", "desc": "Transform data without loops. No for-loops allowed challenge."},
                     {"day": 4, "title": "Objects: Creating, Accessing, Nesting", "type": "coding", "desc": "Build a user profile object. Practice dot vs bracket notation."},
                     {"day": 5, "title": "Destructuring, Spread Operator, Rest Parameters", "type": "coding", "desc": "Simplify code with ES6 features. Merge arrays/objects elegantly."},
                     {"day": 6, "title": "Project: Build a Shopping Cart Data Model", "type": "project", "desc": "Add/remove items, calculate total, apply discounts. Use array methods."},
                     {"day": 7, "title": "Review: JavaScript Best Practices & ESLint", "type": "reading", "desc": "Set up ESLint. Learn clean code principles for JS."},
                 ]},
                {"week_topic": "DOM Manipulation & Events",
                 "tasks": [
                     {"day": 1, "title": "Selecting Elements: getElementById, querySelector", "type": "reading", "desc": "Practice 5 different ways to select elements. Understand NodeList."},
                     {"day": 2, "title": "Modifying Elements: textContent, innerHTML, classList", "type": "coding", "desc": "Build a theme toggler. Change text, add/remove classes dynamically."},
                     {"day": 3, "title": "Creating Elements: createElement, appendChild", "type": "coding", "desc": "Build a dynamic list from array data. Add items to DOM."},
                     {"day": 4, "title": "Event Handling: click, submit, input, keypress", "type": "coding", "desc": "Build a form with real-time validation. Handle keyboard shortcuts."},
                     {"day": 5, "title": "Event Delegation & Bubbling", "type": "coding", "desc": "Handle events on dynamically created elements efficiently."},
                     {"day": 6, "title": "Project: Build an Interactive Todo App", "type": "project", "desc": "Add, delete, toggle, filter todos. Save to localStorage."},
                     {"day": 7, "title": "Review: DOM Performance Optimization", "type": "reading", "desc": "Learn about reflows, batch updates. Use documentFragment."},
                 ]},
                {"week_topic": "Async JavaScript: Promises & Fetch API",
                 "tasks": [
                     {"day": 1, "title": "Understanding Async: Event Loop, Callbacks", "type": "reading", "desc": "Learn call stack, callback queue. Understand callback hell problem."},
                     {"day": 2, "title": "Promises: Creating, Chaining, Error Handling", "type": "coding", "desc": "Convert callbacks to promises. Practice .then(), .catch(), .finally()."},
                     {"day": 3, "title": "Async/Await: Modern Async Syntax", "type": "coding", "desc": "Refactor promises to async/await. Handle errors with try/catch."},
                     {"day": 4, "title": "Fetch API: GET Requests to Public APIs", "type": "coding", "desc": "Fetch data from JSONPlaceholder. Display posts, users, comments."},
                     {"day": 5, "title": "Fetch API: POST, PUT, DELETE Requests", "type": "coding", "desc": "Create, update, delete resources. Build a CRUD interface."},
                     {"day": 6, "title": "Project: Build a Weather App with Real API", "type": "project", "desc": "Use OpenWeatherMap API. Search city, display forecast, handle errors."},
                     {"day": 7, "title": "Review: API Error Handling & Loading States", "type": "reading", "desc": "Add loading spinners, error messages, retry logic."},
                 ]},
            ]
        
        # ============== AI/ML SKILLS ==============
        elif "machine learning" in skill_lower or "ml" in skill_lower:
            return [
                {"week_topic": "Machine Learning Fundamentals & Setup",
                 "tasks": [
                     {"day": 1, "title": "Install Anaconda & Set Up Jupyter Notebook", "type": "coding", "desc": "Download Anaconda, create ML environment. Run first Jupyter notebook."},
                     {"day": 2, "title": "What is Machine Learning: Supervised vs Unsupervised", "type": "reading", "desc": "Learn ML types: classification, regression, clustering. Real-world examples."},
                     {"day": 3, "title": "Python for ML: NumPy Arrays & Operations", "type": "coding", "desc": "Create arrays, reshape, slice. Practice vectorized operations."},
                     {"day": 4, "title": "Data Manipulation with Pandas", "type": "coding", "desc": "Load CSV, filter, group, aggregate data. Handle missing values."},
                     {"day": 5, "title": "Data Visualization: Matplotlib & Seaborn", "type": "coding", "desc": "Create line, bar, scatter, histogram plots. Visualize distributions."},
                     {"day": 6, "title": "Project: Exploratory Data Analysis on Titanic Dataset", "type": "project", "desc": "Load Titanic data, clean, visualize, find patterns. Write insights."},
                     {"day": 7, "title": "Review: ML Workflow & Best Practices", "type": "reading", "desc": "Learn data pipeline: collect, clean, explore, model, evaluate."},
                 ]},
                {"week_topic": "Supervised Learning: Linear & Logistic Regression",
                 "tasks": [
                     {"day": 1, "title": "Linear Regression: Theory & Math", "type": "reading", "desc": "Understand y = mx + b, cost function, gradient descent. Draw intuitions."},
                     {"day": 2, "title": "Implement Linear Regression with Scikit-learn", "type": "coding", "desc": "Load Boston housing data, train model, predict prices. Evaluate with MSE, R²."},
                     {"day": 3, "title": "Feature Engineering: Scaling, Encoding", "type": "coding", "desc": "Use StandardScaler, OneHotEncoder. Handle categorical variables."},
                     {"day": 4, "title": "Logistic Regression: Binary Classification", "type": "reading", "desc": "Understand sigmoid function, decision boundary. When to use logistic."},
                     {"day": 5, "title": "Implement Logistic Regression: Spam Detection", "type": "coding", "desc": "Build spam classifier. Evaluate with accuracy, precision, recall, F1."},
                     {"day": 6, "title": "Project: Predict House Prices", "type": "project", "desc": "Use Kaggle housing dataset. Feature engineering, model training, submission."},
                     {"day": 7, "title": "Review: Overfitting, Underfitting, Regularization", "type": "reading", "desc": "Understand bias-variance tradeoff. L1 and L2 regularization."},
                 ]},
                {"week_topic": "Classification: Decision Trees & Random Forests",
                 "tasks": [
                     {"day": 1, "title": "Decision Trees: How They Work", "type": "reading", "desc": "Understand splits, entropy, information gain. Visualize tree structure."},
                     {"day": 2, "title": "Implement Decision Tree Classifier", "type": "coding", "desc": "Build iris flower classifier. Tune max_depth, min_samples_split."},
                     {"day": 3, "title": "Ensemble Methods: Bagging & Boosting", "type": "reading", "desc": "Understand how multiple models improve accuracy. Random Forest intuition."},
                     {"day": 4, "title": "Random Forest Classifier", "type": "coding", "desc": "Build credit card fraud detector. Handle imbalanced data with SMOTE."},
                     {"day": 5, "title": "Model Evaluation: Confusion Matrix, ROC-AUC", "type": "coding", "desc": "Plot confusion matrix, ROC curve. Understand AUC score."},
                     {"day": 6, "title": "Project: Customer Churn Prediction", "type": "project", "desc": "Predict which customers will leave. Feature importance analysis."},
                     {"day": 7, "title": "Review: Cross-Validation & Hyperparameter Tuning", "type": "reading", "desc": "Use GridSearchCV, RandomizedSearchCV. K-fold cross validation."},
                 ]},
                {"week_topic": "Unsupervised Learning: Clustering & Dimensionality Reduction",
                 "tasks": [
                     {"day": 1, "title": "K-Means Clustering: Theory & Algorithm", "type": "reading", "desc": "Understand centroids, iterations. Elbow method for choosing K."},
                     {"day": 2, "title": "Implement K-Means: Customer Segmentation", "type": "coding", "desc": "Segment customers by behavior. Visualize clusters in 2D."},
                     {"day": 3, "title": "Hierarchical Clustering & DBSCAN", "type": "coding", "desc": "Compare clustering algorithms. When to use each method."},
                     {"day": 4, "title": "PCA: Principal Component Analysis", "type": "reading", "desc": "Understand dimensionality reduction. Eigenvalues, explained variance."},
                     {"day": 5, "title": "Implement PCA: Image Compression", "type": "coding", "desc": "Reduce MNIST dimensions. Visualize in 2D with t-SNE."},
                     {"day": 6, "title": "Project: Market Basket Analysis", "type": "project", "desc": "Find product associations. Implement Apriori algorithm."},
                     {"day": 7, "title": "Review: When to Use Supervised vs Unsupervised", "type": "reading", "desc": "Decision framework for choosing ML approach."},
                 ]},
            ]
        
        elif "deep learning" in skill_lower or "neural network" in skill_lower:
            return [
                {"week_topic": "Deep Learning Fundamentals & Neural Networks",
                 "tasks": [
                     {"day": 1, "title": "Install TensorFlow/PyTorch & GPU Setup", "type": "coding", "desc": "Install deep learning framework. Verify GPU detection with CUDA."},
                     {"day": 2, "title": "Neural Network Basics: Perceptron, Activation Functions", "type": "reading", "desc": "Understand neurons, weights, bias. ReLU, Sigmoid, Softmax functions."},
                     {"day": 3, "title": "Forward & Backward Propagation", "type": "reading", "desc": "Understand how networks learn. Chain rule, gradient calculation."},
                     {"day": 4, "title": "Build Your First Neural Network from Scratch", "type": "coding", "desc": "Implement 2-layer network with NumPy. Train on XOR problem."},
                     {"day": 5, "title": "Neural Network with TensorFlow/Keras", "type": "coding", "desc": "Build Sequential model. Train on MNIST digits classification."},
                     {"day": 6, "title": "Project: Handwritten Digit Recognizer", "type": "project", "desc": "Build CNN for MNIST. Achieve 98%+ accuracy. Save and load model."},
                     {"day": 7, "title": "Review: Loss Functions & Optimizers", "type": "reading", "desc": "Understand MSE, Cross-Entropy. Adam, SGD, RMSprop optimizers."},
                 ]},
                {"week_topic": "Convolutional Neural Networks (CNNs)",
                 "tasks": [
                     {"day": 1, "title": "CNN Architecture: Convolution, Pooling, Flatten", "type": "reading", "desc": "Understand filters, feature maps. Max pooling, stride, padding."},
                     {"day": 2, "title": "Build CNN for Image Classification", "type": "coding", "desc": "Classify CIFAR-10 images. Add Conv2D, MaxPooling, Dense layers."},
                     {"day": 3, "title": "Data Augmentation & Regularization", "type": "coding", "desc": "Prevent overfitting with augmentation, dropout, batch normalization."},
                     {"day": 4, "title": "Transfer Learning: Using Pre-trained Models", "type": "coding", "desc": "Use VGG16, ResNet for custom classification. Fine-tune layers."},
                     {"day": 5, "title": "Visualizing CNN: Feature Maps & Grad-CAM", "type": "coding", "desc": "Understand what CNN sees. Visualize activations and attention."},
                     {"day": 6, "title": "Project: Build a Dog vs Cat Classifier", "type": "project", "desc": "Use transfer learning, achieve 95%+ accuracy. Deploy as web app."},
                     {"day": 7, "title": "Review: CNN Architectures: LeNet, AlexNet, VGG, ResNet", "type": "reading", "desc": "Understand evolution of CNN architectures."},
                 ]},
            ]
        
        elif "nlp" in skill_lower or "natural language" in skill_lower:
            return [
                {"week_topic": "NLP Fundamentals & Text Processing",
                 "tasks": [
                     {"day": 1, "title": "Install NLTK, spaCy & Download Resources", "type": "coding", "desc": "Set up NLP libraries. Download stopwords, models, corpora."},
                     {"day": 2, "title": "Text Preprocessing: Tokenization, Lowercasing, Cleaning", "type": "reading", "desc": "Clean text data. Remove punctuation, numbers, special characters."},
                     {"day": 3, "title": "Stopword Removal & Stemming/Lemmatization", "type": "coding", "desc": "Reduce words to root form. Compare Porter, Lancaster, WordNet."},
                     {"day": 4, "title": "Bag of Words & TF-IDF", "type": "coding", "desc": "Convert text to vectors. Understand term frequency, document frequency."},
                     {"day": 5, "title": "Word Embeddings: Word2Vec, GloVe", "type": "coding", "desc": "Understand semantic similarity. Find similar words, analogies."},
                     {"day": 6, "title": "Project: Build a Text Classifier (Spam Detection)", "type": "project", "desc": "Preprocess emails, TF-IDF features, train Naive Bayes classifier."},
                     {"day": 7, "title": "Review: NLP Pipeline Best Practices", "type": "reading", "desc": "End-to-end text processing workflow."},
                 ]},
                {"week_topic": "Advanced NLP: Transformers & BERT",
                 "tasks": [
                     {"day": 1, "title": "Attention Mechanism: Self-Attention Explained", "type": "reading", "desc": "Understand query, key, value. Why attention revolutionized NLP."},
                     {"day": 2, "title": "Transformer Architecture", "type": "reading", "desc": "Encoder-decoder structure. Positional encoding, multi-head attention."},
                     {"day": 3, "title": "Introduction to BERT", "type": "reading", "desc": "Understand pre-training, fine-tuning. Masked language modeling."},
                     {"day": 4, "title": "Using Hugging Face Transformers", "type": "coding", "desc": "Load pre-trained BERT. Tokenize text, get embeddings."},
                     {"day": 5, "title": "Fine-tune BERT for Classification", "type": "coding", "desc": "Fine-tune on sentiment analysis. Use Trainer API."},
                     {"day": 6, "title": "Project: Build a Sentiment Analysis API", "type": "project", "desc": "Fine-tune BERT, create Flask API. Deploy and test."},
                     {"day": 7, "title": "Review: GPT, T5, and Modern LLMs", "type": "reading", "desc": "Understand differences between encoder, decoder, encoder-decoder models."},
                 ]},
            ]
        
        elif "tensorflow" in skill_lower or "keras" in skill_lower:
            return [
                {"week_topic": "TensorFlow & Keras Fundamentals",
                 "tasks": [
                     {"day": 1, "title": "Install TensorFlow & Verify GPU Support", "type": "coding", "desc": "pip install tensorflow. Check tf.config.list_physical_devices('GPU')."},
                     {"day": 2, "title": "Tensors: Creating, Indexing, Operations", "type": "reading", "desc": "Understand tf.constant, tf.Variable. Shape, dtype, operations."},
                     {"day": 3, "title": "Keras Sequential API: Building Models", "type": "coding", "desc": "Create model with Dense, Activation layers. Compile and summary."},
                     {"day": 4, "title": "Training Models: fit(), Callbacks, History", "type": "coding", "desc": "Train model, use EarlyStopping, ModelCheckpoint. Plot training curves."},
                     {"day": 5, "title": "Keras Functional API: Complex Architectures", "type": "coding", "desc": "Build multi-input, multi-output models. Shared layers."},
                     {"day": 6, "title": "Project: Build and Deploy Image Classifier", "type": "project", "desc": "Train CNN, save model, create TF Serving endpoint."},
                     {"day": 7, "title": "Review: TensorFlow Ecosystem: TFX, TF Lite", "type": "reading", "desc": "Production ML pipeline, mobile deployment."},
                 ]},
            ]
        
        elif "pytorch" in skill_lower:
            return [
                {"week_topic": "PyTorch Fundamentals",
                 "tasks": [
                     {"day": 1, "title": "Install PyTorch & Verify CUDA Support", "type": "coding", "desc": "Install PyTorch with CUDA. Check torch.cuda.is_available()."},
                     {"day": 2, "title": "Tensors: Creation, Operations, GPU Transfer", "type": "reading", "desc": "torch.tensor(), operations. Move to GPU with .cuda() or .to(device)."},
                     {"day": 3, "title": "Autograd: Automatic Differentiation", "type": "coding", "desc": "Understand requires_grad, backward(). Compute gradients."},
                     {"day": 4, "title": "Building Neural Networks with nn.Module", "type": "coding", "desc": "Create custom model class. Forward method, layer definitions."},
                     {"day": 5, "title": "Training Loop: Loss, Optimizer, Backprop", "type": "coding", "desc": "Write complete training loop. optimizer.zero_grad(), loss.backward()."},
                     {"day": 6, "title": "Project: MNIST Classifier with PyTorch", "type": "project", "desc": "Build CNN, train on MNIST, achieve 99% accuracy. Save model."},
                     {"day": 7, "title": "Review: PyTorch Lightning for Clean Code", "type": "reading", "desc": "Simplify training with Lightning. Callbacks, logging."},
                 ]},
            ]
        
        elif "pandas" in skill_lower or "data analysis" in skill_lower:
            return [
                {"week_topic": "Pandas for Data Analysis",
                 "tasks": [
                     {"day": 1, "title": "Install Pandas & Load Your First DataFrame", "type": "coding", "desc": "pip install pandas. Read CSV, Excel files. Explore with head(), info()."},
                     {"day": 2, "title": "Selecting Data: loc, iloc, Boolean Indexing", "type": "reading", "desc": "Select rows, columns. Filter with conditions. Practice 10 exercises."},
                     {"day": 3, "title": "Data Cleaning: Missing Values, Duplicates", "type": "coding", "desc": "isna(), fillna(), dropna(). Remove duplicates with drop_duplicates()."},
                     {"day": 4, "title": "Data Transformation: apply, map, groupby", "type": "coding", "desc": "Apply functions to columns. Group and aggregate data."},
                     {"day": 5, "title": "Merging & Joining DataFrames", "type": "coding", "desc": "merge(), concat(), join(). Inner, outer, left, right joins."},
                     {"day": 6, "title": "Project: Analyze Sales Data", "type": "project", "desc": "Load sales CSV, clean, analyze trends, create summary report."},
                     {"day": 7, "title": "Review: Pandas Performance Tips", "type": "reading", "desc": "Vectorization vs loops. Use categorical dtype. Memory optimization."},
                 ]},
            ]
        
        elif "numpy" in skill_lower:
            return [
                {"week_topic": "NumPy for Scientific Computing",
                 "tasks": [
                     {"day": 1, "title": "Install NumPy & Create Arrays", "type": "coding", "desc": "np.array(), np.zeros(), np.ones(), np.arange(). Understand ndarray."},
                     {"day": 2, "title": "Array Indexing & Slicing", "type": "reading", "desc": "1D, 2D, 3D indexing. Boolean indexing. Fancy indexing."},
                     {"day": 3, "title": "Array Operations: Broadcasting, Vectorization", "type": "coding", "desc": "Element-wise operations. Understand broadcasting rules."},
                     {"day": 4, "title": "Linear Algebra: dot, matmul, transpose, inverse", "type": "coding", "desc": "Matrix multiplication, solve linear systems. Eigenvalues."},
                     {"day": 5, "title": "Statistics: mean, std, percentile, histogram", "type": "coding", "desc": "Compute statistics. Generate random numbers with np.random."},
                     {"day": 6, "title": "Project: Image Processing with NumPy", "type": "project", "desc": "Load image as array, manipulate pixels, apply filters."},
                     {"day": 7, "title": "Review: NumPy vs Python Lists Performance", "type": "reading", "desc": "Benchmark comparisons. When to use NumPy."},
                 ]},
            ]
        
        # ============== DATA SCIENCE & VISUALIZATION ==============
        elif "visualization" in skill_lower or "matplotlib" in skill_lower or "seaborn" in skill_lower:
            return [
                {"week_topic": "Data Visualization with Matplotlib & Seaborn",
                 "tasks": [
                     {"day": 1, "title": "Matplotlib Basics: figure, axes, plot()", "type": "coding", "desc": "Create line plots. Customize title, labels, legend. Save figures."},
                     {"day": 2, "title": "Bar Charts, Histograms & Pie Charts", "type": "coding", "desc": "Visualize categorical data. Customize colors, add annotations."},
                     {"day": 3, "title": "Scatter Plots & Subplots", "type": "coding", "desc": "Visualize relationships. Create multi-plot figures with subplots."},
                     {"day": 4, "title": "Seaborn: Statistical Visualizations", "type": "reading", "desc": "sns.barplot, boxplot, violinplot. Heatmaps for correlations."},
                     {"day": 5, "title": "Advanced: FacetGrid, PairPlot, Custom Styles", "type": "coding", "desc": "Multi-faceted visualizations. Apply themes and palettes."},
                     {"day": 6, "title": "Project: Create an EDA Report with Visualizations", "type": "project", "desc": "Analyze dataset, create 10 insightful charts, write narrative."},
                     {"day": 7, "title": "Review: Choosing the Right Chart Type", "type": "reading", "desc": "Decision guide for visualization types. Best practices."},
                 ]},
            ]
        
        elif "sql" in skill_lower or "database" in skill_lower:
            return [
                {"week_topic": "SQL Fundamentals: Queries & Data Manipulation",
                 "tasks": [
                     {"day": 1, "title": "Install PostgreSQL & pgAdmin/DBeaver", "type": "coding", "desc": "Set up local database. Create your first database and table."},
                     {"day": 2, "title": "SELECT Basics: Columns, WHERE, ORDER BY", "type": "reading", "desc": "Query data with conditions. Sort results. LIMIT clause."},
                     {"day": 3, "title": "INSERT, UPDATE, DELETE Operations", "type": "coding", "desc": "Add, modify, remove data. Understand transactions."},
                     {"day": 4, "title": "JOINs: INNER, LEFT, RIGHT, FULL OUTER", "type": "coding", "desc": "Combine tables. Understand relationships. Practice with 10 exercises."},
                     {"day": 5, "title": "Aggregations: GROUP BY, HAVING, COUNT, SUM, AVG", "type": "coding", "desc": "Summarize data. Filter groups. Calculate statistics."},
                     {"day": 6, "title": "Project: Design and Query an E-commerce Database", "type": "project", "desc": "Create users, products, orders tables. Write 10 business queries."},
                     {"day": 7, "title": "Review: Query Optimization & Indexes", "type": "reading", "desc": "EXPLAIN ANALYZE. Create indexes. Best practices."},
                 ]},
            ]
        
        # ============== WEB FRAMEWORKS ==============
        elif "react" in skill_lower:
            return [
                {"week_topic": "React Fundamentals: Components & JSX",
                 "tasks": [
                     {"day": 1, "title": "Set Up React with Vite or Create React App", "type": "coding", "desc": "npm create vite@latest. Understand project structure. Run dev server."},
                     {"day": 2, "title": "JSX: Writing HTML in JavaScript", "type": "reading", "desc": "Embed expressions, conditional rendering. Map through arrays."},
                     {"day": 3, "title": "Components: Function Components, Composition", "type": "coding", "desc": "Create Header, Footer, Card components. Nest components."},
                     {"day": 4, "title": "Props: Passing Data to Components", "type": "coding", "desc": "Pass props, destructure, default values. PropTypes validation."},
                     {"day": 5, "title": "Styling: CSS Modules, Styled-Components, Tailwind", "type": "coding", "desc": "Compare styling approaches. Set up Tailwind CSS."},
                     {"day": 6, "title": "Project: Build a Static Blog with Components", "type": "project", "desc": "Header, BlogPost, Footer components. Display list of posts."},
                     {"day": 7, "title": "Review: React DevTools & Component Patterns", "type": "reading", "desc": "Debug with React DevTools. Container vs Presentational."},
                 ]},
                {"week_topic": "React State & Hooks",
                 "tasks": [
                     {"day": 1, "title": "useState: Managing Component State", "type": "reading", "desc": "Create counter, toggle, form state. Understand state immutability."},
                     {"day": 2, "title": "Handling Events: onClick, onChange, onSubmit", "type": "coding", "desc": "Build interactive form. Controlled inputs pattern."},
                     {"day": 3, "title": "useEffect: Side Effects & Lifecycle", "type": "coding", "desc": "Fetch data on mount. Update document title. Cleanup effects."},
                     {"day": 4, "title": "Lifting State Up: Sharing State", "type": "coding", "desc": "Parent-child state communication. Temperature converter."},
                     {"day": 5, "title": "useContext: Global State Without Prop Drilling", "type": "coding", "desc": "Create theme context. Provide and consume context."},
                     {"day": 6, "title": "Project: Build a Todo App with Hooks", "type": "project", "desc": "Add, delete, toggle, filter todos. Persist to localStorage."},
                     {"day": 7, "title": "Review: Rules of Hooks & Common Mistakes", "type": "reading", "desc": "Avoid infinite loops, stale closures. Dependency arrays."},
                 ]},
            ]
        
        elif "node" in skill_lower or "express" in skill_lower:
            return [
                {"week_topic": "Node.js & Express Fundamentals",
                 "tasks": [
                     {"day": 1, "title": "Install Node.js & Create First Script", "type": "coding", "desc": "Download Node.js, run node --version. Create hello.js with console.log."},
                     {"day": 2, "title": "npm & package.json: Managing Dependencies", "type": "reading", "desc": "npm init, install, uninstall. Understand dependencies vs devDependencies."},
                     {"day": 3, "title": "Express.js: Create Your First Server", "type": "coding", "desc": "Install Express, create server on port 3000. Handle GET request."},
                     {"day": 4, "title": "Routing: params, query, body", "type": "coding", "desc": "Create routes /users, /users/:id. Parse request body with express.json()."},
                     {"day": 5, "title": "Middleware: Built-in, Custom, Error Handling", "type": "coding", "desc": "Create logging middleware. Handle 404 and errors globally."},
                     {"day": 6, "title": "Project: Build a REST API for Todos", "type": "project", "desc": "CRUD endpoints: GET, POST, PUT, DELETE. Store in memory array."},
                     {"day": 7, "title": "Review: API Testing with Postman", "type": "reading", "desc": "Test all endpoints. Create Postman collection."},
                 ]},
            ]
        
        elif "django" in skill_lower:
            return [
                {"week_topic": "Django Web Framework Fundamentals",
                 "tasks": [
                     {"day": 1, "title": "Install Django & Create Project", "type": "coding", "desc": "pip install django. django-admin startproject. Run development server."},
                     {"day": 2, "title": "Django Apps, URLs & Views", "type": "reading", "desc": "Create app, define URL patterns. Function-based views."},
                     {"day": 3, "title": "Templates: Rendering HTML", "type": "coding", "desc": "Create templates folder, extend base.html. Template tags and filters."},
                     {"day": 4, "title": "Models: Database with Django ORM", "type": "coding", "desc": "Define models, make migrations. Create, read, update, delete objects."},
                     {"day": 5, "title": "Forms: User Input & Validation", "type": "coding", "desc": "Django forms, ModelForms. Validate and save data."},
                     {"day": 6, "title": "Project: Build a Blog Application", "type": "project", "desc": "Posts, comments, user auth. List, detail, create views."},
                     {"day": 7, "title": "Review: Django Admin & Best Practices", "type": "reading", "desc": "Customize admin. Project structure best practices."},
                 ]},
            ]
        
        elif "flask" in skill_lower:
            return [
                {"week_topic": "Flask Web Framework Fundamentals",
                 "tasks": [
                     {"day": 1, "title": "Install Flask & Create Hello World App", "type": "coding", "desc": "pip install flask. Create app.py with @app.route. Run with flask run."},
                     {"day": 2, "title": "Routing & HTTP Methods", "type": "reading", "desc": "Define routes with decorators. Handle GET, POST, PUT, DELETE."},
                     {"day": 3, "title": "Templates with Jinja2", "type": "coding", "desc": "Render templates, pass data. Template inheritance with extends."},
                     {"day": 4, "title": "Forms & Request Data", "type": "coding", "desc": "Handle form submissions. Access request.form, request.args."},
                     {"day": 5, "title": "SQLAlchemy: Database Integration", "type": "coding", "desc": "Set up Flask-SQLAlchemy. Define models, CRUD operations."},
                     {"day": 6, "title": "Project: Build a URL Shortener", "type": "project", "desc": "Create short URLs, redirect to original. Track click counts."},
                     {"day": 7, "title": "Review: Flask Blueprints & Project Structure", "type": "reading", "desc": "Organize large apps with blueprints. Best practices."},
                 ]},
            ]
        
        # ============== DEVOPS & CLOUD ==============
        elif "docker" in skill_lower:
            return [
                {"week_topic": "Docker Containerization Fundamentals",
                 "tasks": [
                     {"day": 1, "title": "Install Docker Desktop & Run First Container", "type": "coding", "desc": "Download Docker Desktop. Run docker run hello-world. Understand images vs containers."},
                     {"day": 2, "title": "Docker Commands: run, ps, stop, rm, images", "type": "reading", "desc": "Manage containers and images. Practice with nginx, python images."},
                     {"day": 3, "title": "Dockerfile: Build Custom Images", "type": "coding", "desc": "Create Dockerfile with FROM, COPY, RUN, CMD. Build and tag image."},
                     {"day": 4, "title": "Docker Volumes & Networks", "type": "coding", "desc": "Persist data with volumes. Connect containers with networks."},
                     {"day": 5, "title": "Docker Compose: Multi-Container Apps", "type": "coding", "desc": "Create docker-compose.yml. Define services, volumes, networks."},
                     {"day": 6, "title": "Project: Containerize a Full Stack App", "type": "project", "desc": "Dockerize frontend, backend, database. Use docker-compose."},
                     {"day": 7, "title": "Review: Docker Best Practices & Security", "type": "reading", "desc": "Multi-stage builds, .dockerignore. Non-root users."},
                 ]},
            ]
        
        elif "kubernetes" in skill_lower or "k8s" in skill_lower:
            return [
                {"week_topic": "Kubernetes Fundamentals",
                 "tasks": [
                     {"day": 1, "title": "Install minikube or kind for Local K8s", "type": "coding", "desc": "Set up local cluster. kubectl get nodes. Understand K8s architecture."},
                     {"day": 2, "title": "Pods: The Smallest Deployable Unit", "type": "reading", "desc": "Create pod YAML. kubectl apply, get, describe, logs. Pod lifecycle."},
                     {"day": 3, "title": "Deployments: Scaling & Rolling Updates", "type": "coding", "desc": "Create deployment. Scale replicas. Perform rolling update."},
                     {"day": 4, "title": "Services: Exposing Applications", "type": "coding", "desc": "ClusterIP, NodePort, LoadBalancer. Service discovery."},
                     {"day": 5, "title": "ConfigMaps & Secrets", "type": "coding", "desc": "Externalize configuration. Store sensitive data securely."},
                     {"day": 6, "title": "Project: Deploy a Web App to Kubernetes", "type": "project", "desc": "Deploy frontend, backend with services. Use Ingress for routing."},
                     {"day": 7, "title": "Review: K8s Architecture & Best Practices", "type": "reading", "desc": "Control plane, worker nodes. Resource limits, health checks."},
                 ]},
            ]
        
        elif "aws" in skill_lower:
            return [
                {"week_topic": "AWS Cloud Fundamentals",
                 "tasks": [
                     {"day": 1, "title": "Create AWS Free Tier Account & Set Up IAM User", "type": "coding", "desc": "Create account, enable MFA. Create IAM user with programmatic access."},
                     {"day": 2, "title": "EC2: Launch Your First Virtual Server", "type": "reading", "desc": "Launch t2.micro instance. SSH connect. Security groups."},
                     {"day": 3, "title": "S3: Object Storage for Files", "type": "coding", "desc": "Create bucket, upload files. Set permissions. Static website hosting."},
                     {"day": 4, "title": "RDS: Managed Relational Database", "type": "coding", "desc": "Launch PostgreSQL RDS instance. Connect from application."},
                     {"day": 5, "title": "Lambda: Serverless Functions", "type": "coding", "desc": "Create Lambda function. Trigger with API Gateway."},
                     {"day": 6, "title": "Project: Deploy a Web App to AWS", "type": "project", "desc": "EC2 for app, RDS for database, S3 for assets. Use Elastic Beanstalk."},
                     {"day": 7, "title": "Review: AWS Well-Architected Framework", "type": "reading", "desc": "Security, reliability, performance, cost optimization pillars."},
                 ]},
            ]
        
        elif "git" in skill_lower or "version control" in skill_lower:
            return [
                {"week_topic": "Git Version Control Fundamentals",
                 "tasks": [
                     {"day": 1, "title": "Install Git & Configure User Settings", "type": "coding", "desc": "git config user.name, user.email. Understand .gitconfig."},
                     {"day": 2, "title": "Basic Commands: init, add, commit, status, log", "type": "reading", "desc": "Create repo, stage changes, commit. View history with git log."},
                     {"day": 3, "title": "Branching & Merging", "type": "coding", "desc": "Create feature branches. Merge changes. Resolve conflicts."},
                     {"day": 4, "title": "Remote Repositories: push, pull, clone, fetch", "type": "coding", "desc": "Connect to GitHub. Push changes, pull updates. Upstream tracking."},
                     {"day": 5, "title": "Pull Requests & Code Review", "type": "coding", "desc": "Fork repo, create PR. Review changes. Merge PR."},
                     {"day": 6, "title": "Project: Collaborate on a GitHub Project", "type": "project", "desc": "Fork, clone, make changes, create PR. Review others' PRs."},
                     {"day": 7, "title": "Review: Git Workflow Best Practices", "type": "reading", "desc": "GitFlow, GitHub Flow. Commit message conventions."},
                 ]},
            ]
        
        # ============== DEFAULT FOR ANY OTHER SKILL ==============
        else:
            # Generate dynamic curriculum for any skill
            return [
                {"week_topic": f"{skill_name} Fundamentals: Core Concepts",
                 "tasks": [
                     {"day": 1, "title": f"Set Up {skill_name} Development Environment", "type": "coding", "desc": f"Install necessary tools and IDEs for {skill_name}. Verify setup with a simple test."},
                     {"day": 2, "title": f"{skill_name} Core Concepts: Theory & Basics", "type": "reading", "desc": f"Read official documentation. Understand fundamental concepts of {skill_name}."},
                     {"day": 3, "title": f"{skill_name} Hands-on: First Exercise", "type": "coding", "desc": f"Apply basic concepts of {skill_name} with guided exercises."},
                     {"day": 4, "title": f"{skill_name} Practice: 5 Beginner Challenges", "type": "coding", "desc": f"Solve beginner-level problems using {skill_name}. Build muscle memory."},
                     {"day": 5, "title": f"{skill_name} Practice: 5 Intermediate Challenges", "type": "coding", "desc": f"Level up with more complex {skill_name} problems."},
                     {"day": 6, "title": f"Project: Build a Mini Project with {skill_name}", "type": "project", "desc": f"Apply {skill_name} knowledge to build a small but complete project."},
                     {"day": 7, "title": f"Review: {skill_name} Best Practices", "type": "reading", "desc": f"Learn industry best practices for {skill_name}. Document learnings."},
                 ]},
                {"week_topic": f"{skill_name} Intermediate: Building Skills",
                 "tasks": [
                     {"day": 1, "title": f"Advanced {skill_name} Concepts", "type": "reading", "desc": f"Deep dive into advanced features and patterns of {skill_name}."},
                     {"day": 2, "title": f"{skill_name} Common Patterns & Techniques", "type": "coding", "desc": f"Learn and practice common patterns used in {skill_name}."},
                     {"day": 3, "title": f"{skill_name} Error Handling & Debugging", "type": "coding", "desc": f"Learn to debug and handle errors effectively in {skill_name}."},
                     {"day": 4, "title": f"{skill_name} Performance & Optimization", "type": "coding", "desc": f"Optimize your {skill_name} code for better performance."},
                     {"day": 5, "title": f"{skill_name} Testing & Quality", "type": "coding", "desc": f"Write tests for your {skill_name} code. Ensure quality."},
                     {"day": 6, "title": f"Project: Build a Real-World {skill_name} Application", "type": "project", "desc": f"Create a production-ready application using {skill_name}."},
                     {"day": 7, "title": f"Review: {skill_name} Portfolio & Documentation", "type": "reading", "desc": f"Document your {skill_name} projects. Update portfolio."},
                 ]},
            ]
    
    def _generate_generic_week(self, target_role: str, week_num: int, phase: Dict[str, Any], daily_minutes: int) -> Dict[str, Any]:
        """Generate a detailed week based on skill curriculum - TRULY DYNAMIC."""
        phase_skills = phase.get("skills", ["Core Skills"])
        week_in_phase = week_num - phase["start_week"]
        
        # Get the skill for this week
        skill_index = week_in_phase % len(phase_skills)
        current_skill = phase_skills[skill_index]
        
        # Get the detailed curriculum for this skill
        skill_curriculum = self._get_skill_curriculum(current_skill)
        
        # Determine which week of this skill we're on
        weeks_per_skill = len(skill_curriculum)
        skill_week_index = (week_in_phase // len(phase_skills)) % weeks_per_skill
        
        if skill_week_index < len(skill_curriculum):
            week_data = skill_curriculum[skill_week_index]
        else:
            week_data = skill_curriculum[0]  # Fallback to first week
        
        # Build days from curriculum
        days = []
        for task_info in week_data["tasks"]:
            days.append({
                "day_number": task_info["day"],
                "tasks": [{
                    "title": task_info["title"],
                    "description": task_info["desc"],
                    "task_type": task_info["type"],
                    "estimated_duration": daily_minutes,
                    "difficulty": phase["phase_number"] + 1,
                    "learning_objectives": [f"Complete: {task_info['title']}"],
                    "success_criteria": "Task completed successfully",
                    "prerequisites": [],
                    "resources": self._get_resources_for_topic(current_skill)
                }]
            })
        
        return {
            "week_number": week_num,
            "focus_area": f"Week {week_num}: {week_data['week_topic']}",
            "learning_objectives": [f"Master {current_skill} concepts covered this week"],
            "days": days
        }
    
    def _generate_generic_phase_weeks(
        self,
        target_role: str,
        phase: Dict[str, Any],
        daily_minutes: int
    ) -> Dict[str, Any]:
        """Generate weeks for any phase using the dynamic skill curriculum system."""
        weeks = []
        phase_skills = phase.get("skills", ["Core Skills"])
        
        for week_num in range(phase["start_week"], phase["end_week"] + 1):
            weeks.append(self._generate_generic_week(target_role, week_num, phase, daily_minutes))
        
        return {
            "weeks": weeks,
            "milestones": [{
                "week_number": phase["end_week"],
                "title": f"{phase['phase_name']} Complete: Mastered {', '.join(phase_skills[:3])}",
                "description": f"Completed {phase['phase_name']} with hands-on projects",
                "skills_demonstrated": phase_skills,
                "deliverable": "Working projects demonstrating skill mastery"
            }]
        }
    
    def _get_task_templates_for_role(self, target_role: str, skills: List[str]) -> Dict[str, Any]:
        """Get specific task templates with real resources based on role and skills."""
        templates = {
            "HTML": {
                "project_name": "Personal Portfolio Page",
                "intro_resources": [
                    {"title": "MDN HTML Basics", "url": "https://developer.mozilla.org/en-US/docs/Learn/HTML/Introduction_to_HTML", "type": "documentation"},
                    {"title": "W3Schools HTML Tutorial", "url": "https://www.w3schools.com/html/", "type": "tutorial"}
                ],
                "video_resources": [
                    {"title": "HTML Full Course - freeCodeCamp", "url": "https://www.youtube.com/watch?v=pQN-pnXPaVg", "type": "video"}
                ],
                "practice_resources": [
                    {"title": "freeCodeCamp HTML Exercises", "url": "https://www.freecodecamp.org/learn/2022/responsive-web-design/", "type": "practice"}
                ],
                "project_resources": [
                    {"title": "Build Your First Website", "url": "https://developer.mozilla.org/en-US/docs/Learn/Getting_started_with_the_web", "type": "tutorial"}
                ]
            },
            "CSS": {
                "project_name": "Responsive Landing Page",
                "intro_resources": [
                    {"title": "MDN CSS Basics", "url": "https://developer.mozilla.org/en-US/docs/Learn/CSS/First_steps", "type": "documentation"}
                ],
                "video_resources": [
                    {"title": "CSS Complete Guide - Kevin Powell", "url": "https://www.youtube.com/watch?v=1Rs2ND1ryYc", "type": "video"}
                ],
                "practice_resources": [
                    {"title": "CSS Battle", "url": "https://cssbattle.dev/", "type": "practice"},
                    {"title": "Flexbox Froggy", "url": "https://flexboxfroggy.com/", "type": "practice"}
                ],
                "project_resources": [
                    {"title": "Build a Landing Page", "url": "https://www.freecodecamp.org/learn/2022/responsive-web-design/", "type": "tutorial"}
                ]
            },
            "JavaScript": {
                "project_name": "Interactive To-Do App",
                "intro_resources": [
                    {"title": "JavaScript.info", "url": "https://javascript.info/", "type": "documentation"},
                    {"title": "MDN JavaScript Guide", "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide", "type": "documentation"}
                ],
                "video_resources": [
                    {"title": "JavaScript Crash Course - Traversy Media", "url": "https://www.youtube.com/watch?v=hdI2bqOjy3c", "type": "video"}
                ],
                "practice_resources": [
                    {"title": "JavaScript30", "url": "https://javascript30.com/", "type": "practice"},
                    {"title": "Exercism JavaScript Track", "url": "https://exercism.org/tracks/javascript", "type": "practice"}
                ],
                "project_resources": [
                    {"title": "Build a To-Do App", "url": "https://www.freecodecamp.org/news/build-a-todo-app-with-javascript/", "type": "tutorial"}
                ]
            },
            "React": {
                "project_name": "React Weather Dashboard",
                "intro_resources": [
                    {"title": "React Official Tutorial", "url": "https://react.dev/learn", "type": "documentation"}
                ],
                "video_resources": [
                    {"title": "React Course - freeCodeCamp", "url": "https://www.youtube.com/watch?v=bMknfKXIFA8", "type": "video"}
                ],
                "practice_resources": [
                    {"title": "React Exercises", "url": "https://react.dev/learn/tutorial-tic-tac-toe", "type": "practice"}
                ],
                "project_resources": [
                    {"title": "Build React Projects", "url": "https://www.freecodecamp.org/news/react-projects-for-beginners-easy-ideas-with-code/", "type": "tutorial"}
                ]
            },
            "Python": {
                "project_name": "Python CLI Task Manager",
                "intro_resources": [
                    {"title": "Python Official Tutorial", "url": "https://docs.python.org/3/tutorial/", "type": "documentation"},
                    {"title": "Real Python", "url": "https://realpython.com/python-first-steps/", "type": "tutorial"}
                ],
                "video_resources": [
                    {"title": "Python for Beginners - freeCodeCamp", "url": "https://www.youtube.com/watch?v=rfscVS0vtbw", "type": "video"}
                ],
                "practice_resources": [
                    {"title": "Exercism Python Track", "url": "https://exercism.org/tracks/python", "type": "practice"},
                    {"title": "Python Koans", "url": "https://github.com/gregmalcolm/python_koans", "type": "practice"}
                ],
                "project_resources": [
                    {"title": "Python Projects for Beginners", "url": "https://realpython.com/tutorials/projects/", "type": "tutorial"}
                ]
            },
            "default": {
                "project_name": "Portfolio Project",
                "intro_resources": [{"title": "Documentation", "url": "https://developer.mozilla.org", "type": "documentation"}],
                "video_resources": [{"title": "Tutorial Video", "url": "https://youtube.com", "type": "video"}],
                "practice_resources": [{"title": "Practice", "url": "https://www.freecodecamp.org/learn", "type": "practice"}],
                "project_resources": [{"title": "Project Ideas", "url": "https://github.com/topics/beginner-project", "type": "tutorial"}]
            }
        }
        
        # Build result with templates for each skill
        result = {"default": templates["default"]}
        for skill in skills:
            skill_key = skill.split()[0] if skill else "default"  # Get first word
            for template_key in templates:
                if template_key.lower() in skill.lower():
                    result[skill] = templates[template_key]
                    break
            else:
                result[skill] = templates["default"]
        
        return result
    
    def _get_default_skills_for_role(self, target_role: str) -> List[str]:
        """Get default skills based on target role."""
        role_lower = target_role.lower()
        
        skill_mappings = {
            "frontend": ["HTML5 & Semantic Markup", "CSS3 & Flexbox/Grid", "JavaScript ES6+", "React.js", "TypeScript", "Responsive Design", "Git & GitHub", "Testing with Jest"],
            "front end": ["HTML5 & Semantic Markup", "CSS3 & Flexbox/Grid", "JavaScript ES6+", "React.js", "TypeScript", "Responsive Design", "Git & GitHub", "Testing with Jest"],
            "backend": ["Python/Node.js", "REST API Design", "Database Design (SQL)", "Authentication & Security", "API Documentation", "Caching with Redis", "Git & GitHub", "Docker Basics"],
            "back end": ["Python/Node.js", "REST API Design", "Database Design (SQL)", "Authentication & Security", "API Documentation", "Caching with Redis", "Git & GitHub", "Docker Basics"],
            "fullstack": ["HTML/CSS/JavaScript", "React.js Frontend", "Node.js/Express Backend", "Database (PostgreSQL/MongoDB)", "REST API Development", "Authentication (JWT)", "Git & GitHub", "Docker & Deployment"],
            "full stack": ["HTML/CSS/JavaScript", "React.js Frontend", "Node.js/Express Backend", "Database (PostgreSQL/MongoDB)", "REST API Development", "Authentication (JWT)", "Git & GitHub", "Docker & Deployment"],
            "full-stack": ["HTML/CSS/JavaScript", "React.js Frontend", "Node.js/Express Backend", "Database (PostgreSQL/MongoDB)", "REST API Development", "Authentication (JWT)", "Git & GitHub", "Docker & Deployment"],
            "data scientist": ["Python for Data Science", "Pandas & NumPy", "Data Visualization (Matplotlib/Seaborn)", "Statistics & Probability", "Machine Learning (Scikit-learn)", "SQL for Data Analysis", "Jupyter Notebooks", "Model Deployment"],
            "data analyst": ["SQL & Database Queries", "Excel & Spreadsheets", "Python for Analysis", "Data Visualization", "Statistics Fundamentals", "Tableau/Power BI", "Data Cleaning", "Report Building"],
            "devops": ["Linux Administration", "Docker Containers", "Kubernetes Orchestration", "CI/CD Pipelines", "AWS/Azure Cloud", "Terraform IaC", "Monitoring & Logging", "Scripting (Bash/Python)"],
            "machine learning": ["Python & Libraries", "Mathematics for ML", "Supervised Learning", "Unsupervised Learning", "Deep Learning (TensorFlow/PyTorch)", "Model Evaluation", "Feature Engineering", "MLOps Basics"],
            "ml engineer": ["Python & Libraries", "Mathematics for ML", "Supervised Learning", "Unsupervised Learning", "Deep Learning (TensorFlow/PyTorch)", "Model Evaluation", "Feature Engineering", "MLOps Basics"],
            "mobile": ["React Native/Flutter", "Mobile UI/UX Principles", "State Management", "API Integration", "Local Storage", "Push Notifications", "App Store Deployment", "Mobile Testing"],
            "android": ["Kotlin Programming", "Android Studio", "Android UI/XML", "Jetpack Compose", "Room Database", "Retrofit/APIs", "Material Design", "Google Play Store"],
            "ios": ["Swift Programming", "Xcode IDE", "SwiftUI", "UIKit", "Core Data", "Networking", "App Store Guidelines", "iOS Testing"],
            "cloud": ["AWS Fundamentals", "Azure Services", "Cloud Architecture", "Networking & Security", "Serverless Computing", "Infrastructure as Code", "Cost Optimization", "Multi-Cloud Strategy"],
            "cybersecurity": ["Network Security", "Ethical Hacking", "Cryptography", "Security Tools (Wireshark/Nmap)", "Penetration Testing", "Incident Response", "Compliance (GDPR/SOC2)", "Security Best Practices"],
            "web developer": ["HTML5 & CSS3", "JavaScript Fundamentals", "Responsive Web Design", "React/Vue/Angular", "Backend Basics", "Databases", "Version Control", "Web Security"],
            "software engineer": ["Programming Fundamentals", "Data Structures", "Algorithms", "Object-Oriented Design", "System Design", "Testing & QA", "Version Control", "Software Architecture"],
            "software developer": ["Programming Fundamentals", "Data Structures", "Algorithms", "Object-Oriented Design", "Database Management", "API Development", "Version Control", "Debugging & Testing"],
            "python developer": ["Python Fundamentals", "Object-Oriented Python", "Web Frameworks (Django/Flask)", "Database Integration", "Testing (pytest)", "Package Management", "API Development", "Async Programming"],
            "java developer": ["Java Fundamentals", "Object-Oriented Programming", "Spring Boot", "JPA/Hibernate", "Maven/Gradle", "Unit Testing (JUnit)", "REST APIs", "Microservices"],
            "javascript developer": ["JavaScript ES6+", "DOM Manipulation", "Async Programming", "Node.js", "React/Vue/Angular", "TypeScript", "Testing (Jest)", "Build Tools"],
            "ui/ux": ["Design Principles", "Figma/Sketch", "User Research", "Wireframing", "Prototyping", "Usability Testing", "Design Systems", "Accessibility (a11y)"],
            "product manager": ["Product Strategy", "User Research", "Roadmap Planning", "Agile/Scrum", "Data Analysis", "Stakeholder Management", "Product Metrics", "Go-to-Market"],
            "qa engineer": ["Testing Fundamentals", "Test Case Design", "Manual Testing", "Automation (Selenium/Cypress)", "API Testing", "Performance Testing", "Bug Tracking", "CI/CD Integration"],
            "database": ["SQL Fundamentals", "Database Design", "Query Optimization", "PostgreSQL/MySQL", "MongoDB/NoSQL", "Data Modeling", "Database Administration", "Backup & Recovery"],
        }
        
        # Try to match the role
        for key, skills in skill_mappings.items():
            if key in role_lower:
                return skills
        
        # Default generic tech skills
        return ["Programming Fundamentals", "Problem Solving", "Git Version Control", "Documentation", "Best Practices", "Testing", "Communication", "Project Management"]
    
    def _generate_default_roadmap(
        self, 
        target_role: str, 
        duration_weeks: int,
        daily_minutes: int
    ) -> Dict[str, Any]:
        """Generate a default roadmap structure when AI fails - NOW GENERATES ALL WEEKS."""
        logger.info(f"Generating default roadmap for: {target_role} ({duration_weeks} weeks)")
        
        # Get skills for the role
        skills = self._get_default_skills_for_role(target_role)
        
        # Define phases for the entire duration
        phases = self._define_learning_phases(target_role, duration_weeks, skills, "beginner")
        
        weekly_breakdown = []
        milestones = []
        
        for phase in phases:
            phase_result = self._generate_default_phase_weeks(target_role, phase, daily_minutes)
            weekly_breakdown.extend(phase_result.get("weeks", []))
            milestones.extend(phase_result.get("milestones", []))
        
        return {
            "roadmap_title": f"Your Path to Becoming a {target_role}",
            "description": f"A personalized {duration_weeks}-week learning journey to help you become a {target_role}. "
                          f"This roadmap covers: {', '.join(skills[:6])}",
            "weekly_breakdown": weekly_breakdown,
            "milestones": milestones
        }
    
    def _get_daily_minutes(self, intensity: str, profile: Optional[UserProfile]) -> int:
        """Get daily learning minutes based on intensity."""
        if profile and profile.time_per_day:
            return profile.time_per_day
        
        intensity_map = {
            "low": 30,
            "medium": 60,
            "high": 120
        }
        return intensity_map.get(intensity, 60)
    
    async def regenerate_roadmap(
        self,
        user_id: UUID,
        roadmap_id: UUID,
        feedback: Optional[str] = None,
        adjustments: Optional[Dict] = None
    ) -> Roadmap:
        """Regenerate roadmap with user feedback."""
        logger.info(f"Regenerating roadmap {roadmap_id} for user {user_id}")
        
        # Get existing roadmap
        result = await self.db.execute(
            select(Roadmap).where(
                Roadmap.id == roadmap_id,
                Roadmap.user_id == user_id
            )
        )
        old_roadmap = result.scalar_one_or_none()
        
        if not old_roadmap:
            raise ValueError("Roadmap not found")
        
        logger.info(f"Old roadmap target_role: '{old_roadmap.target_role}'")
        
        # ALWAYS get the current target_role from profile (user may have changed their goal)
        profile_result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = profile_result.scalar_one_or_none()
        
        # Use profile's goal_role if available, otherwise fall back to old roadmap's target_role
        if profile and profile.goal_role and profile.goal_role.lower() != "none":
            target_role = profile.goal_role
            logger.info(f"Using profile's goal_role: '{target_role}'")
        elif old_roadmap.target_role and old_roadmap.target_role.lower() != "none":
            target_role = old_roadmap.target_role
            logger.info(f"Falling back to old roadmap's target_role: '{target_role}'")
        else:
            raise ValueError(
                "Cannot regenerate roadmap: No valid career goal found. Please update your profile first."
            )
        
        # Mark old as abandoned
        old_roadmap.status = "abandoned"
        
        # Generate new with adjustments
        params = old_roadmap.generation_params or {}
        if adjustments:
            params.update(adjustments)
        
        logger.info(f"Generating new roadmap with target_role: '{target_role}'")
        
        new_roadmap = await self.generate_roadmap(
            user_id=user_id,
            target_role=target_role,
            duration_weeks=old_roadmap.total_weeks,
            intensity=params.get("intensity", "medium")
        )
        
        await self.db.commit()
        
        return new_roadmap
