# AIFund-5 Dataset — AI Fundamentals Syllabus for 5 Knowledge Components
# Paper Section 6.1 — University-level AI Course Benchmark

SYLLABUS_UNITS = {
    1: {
        "name": "Agents & ML Intro",
        "topics": [
            "Definition of AI, Turing Test, Chinese Room argument",
            "Intelligent agents: simple reflex, model-based, goal-based, utility-based, learning agents",
            "PEAS framework (Performance, Environment, Actuators, Sensors)",
            "Environment types: fully/partially observable, deterministic/stochastic, episodic/sequential",
            "Machine learning paradigms: supervised, unsupervised, reinforcement learning",
            "Supervised learning: classification vs regression, training/testing split",
            "Overfitting, underfitting, bias-variance tradeoff",
            "Evaluation metrics: accuracy, precision, recall, F1-score, confusion matrix",
        ],
    },
    2: {
        "name": "Search & CSP",
        "topics": [
            "Problem formulation: state space, initial state, goal test, path cost",
            "Uninformed search: BFS, DFS, Uniform Cost Search, Iterative Deepening",
            "Informed search: Greedy Best-First, A* search, admissible heuristics",
            "Heuristic design: Manhattan distance, Euclidean distance, relaxed problems",
            "Local search: Hill climbing, simulated annealing, genetic algorithms",
            "Constraint Satisfaction Problems: variables, domains, constraints",
            "CSP techniques: arc consistency, backtracking, forward checking",
            "Adversarial search: minimax, alpha-beta pruning",
        ],
    },
    3: {
        "name": "Knowledge Representation",
        "topics": [
            "Propositional logic: syntax, semantics, truth tables",
            "Logical connectives: AND, OR, NOT, IMPLIES, BICONDITIONAL",
            "Inference rules: modus ponens, resolution, forward/backward chaining",
            "First-order logic: predicates, quantifiers (∀, ∃), unification",
            "Knowledge representation schemes: semantic networks, frames",
            "Ontologies and description logics",
            "Probabilistic reasoning: Bayes theorem, conditional independence",
            "Bayesian networks: structure, inference, d-separation",
        ],
    },
    4: {
        "name": "Planning & Heuristics",
        "topics": [
            "Classical planning: STRIPS representation, PDDL language",
            "State-space planning: forward search, backward search",
            "Plan-space planning: partial-order planning, least commitment",
            "GraphPlan algorithm: planning graph, mutex relations",
            "Hierarchical task networks (HTN)",
            "Real-world planning: scheduling, resource allocation",
            "Admissible heuristics for planning: relaxed-plan heuristic",
            "Domain-independent heuristics: delete relaxation, landmarks",
        ],
    },
    5: {
        "name": "Learning & Game AI",
        "topics": [
            "Decision trees: ID3, C4.5, information gain, entropy",
            "Ensemble methods: random forests, boosting, bagging",
            "Neural networks: perceptron, backpropagation, activation functions",
            "Deep learning: CNNs, RNNs, transformers (brief overview)",
            "Reinforcement learning: MDP, value functions, Q-learning",
            "Policy gradient methods: REINFORCE, actor-critic",
            "Game playing: minimax with alpha-beta pruning complexity analysis",
            "Monte Carlo Tree Search (MCTS) and AlphaGo approach",
        ],
    },
}

# Difficulty levels (Bloom's Taxonomy mapping)
DIFFICULTY_LABELS = {
    1: "Recall",
    2: "Understand",
    3: "Apply",
    4: "Analyze",
    5: "Create/Evaluate",
}
