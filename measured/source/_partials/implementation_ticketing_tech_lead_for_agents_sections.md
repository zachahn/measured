Because an agent — not a human teammate — will pick up each task, give every task file these three additional sections after the ones above. They remove the paralysis of staring at a large codebase and let the agent check its own progress.

## Entry Point

Where exactly do they start? Name the file, class, or function. "Start in `src/middleware/auth.ts` — there's already a pattern there for request validation you can follow." Removes the paralysis of staring at a large codebase.

## Step-by-Step Approach

An ordered checklist of logical steps — not pseudocode. Break the work into 4–8 discrete steps. Not implementation details, but the thinking sequence: "1. Write the failing test first. 2. Add the middleware function. 3. Wire it into the router. 4. Verify manually with curl." Lets them check progress and catch if they've gone off-track early.

## Patterns to Follow

Point to an existing ticket, PR, or file that solved a similar problem. "`src/payments.ts` did something nearly identical for the `/api/payments` route — use that as a reference." Learning by analogy is faster than learning from scratch.
