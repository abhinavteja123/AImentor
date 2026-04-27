# Consent & Data Handling Template

Use this document as the basis for IRB / institutional-review submissions when
collecting real user utterances or recruiter-labeled resume/JD pairs for the
AImentor evaluation effort.

## Purpose
You are being asked to contribute labeled text samples that will help evaluate
an AI career-mentoring system named AImentor. The data will be used solely for
academic research and will appear in an IEEE conference submission.

## What we collect
- **Intent-annotation study**: your free-text message to a mentor chatbot and a
  single chosen label from eight predefined intents (no follow-up profile data).
- **Resume/JD study**: two documents (a resume and a job description) plus an
  integer match score you assign. Resumes will be redacted of name, email,
  phone, URL, and government-ID numbers *before* storage.

## How data will be used
- Stored in hashed-ID form only.
- Used to train/evaluate classifiers and retrieval models.
- Released only in redacted, synthetic-substituted form; raw samples never leave
  the research team's machine.
- Deleted upon request at any time by emailing the corresponding author.

## Compensation
Annotators are paid the prevailing local minimum-wage equivalent per hour of
annotation, computed from the median completion time of a calibration batch of
ten samples.

## Risks
Minimal. All shared artifacts pass through the redactor in
`backend/research/ethics/pii_redactor.py` before disk write.

## Rights
You may withdraw consent at any time. Withdrawal triggers deletion of your
samples and a re-computation of affected numbers; a corrigendum will be filed
if results have already been submitted.

## Contact
_Corresponding author_: <to be filled>
_IRB reference_: <to be filled>

I have read and understood the above:

Signature: ____________________  Date: ____________
