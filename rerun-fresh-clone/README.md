# Fresh-clone re-run (2026-10-10)

What a judge does, done by us first: `gh repo clone jdingus/dig-risk-control` into an empty folder, then
`python3 run.py --preflight` and, for each arm, `python3 run.py <arm> --reps 1 --out rerun/<arm>`.
The clone was at commit bec716b, which ships the v1 folder. 15 questions x 1 run x 3 arms = 45 answers, copied
here unedited from the clone's rerun/ folder. Same machine as the committed runs (the cloud environment could
not start the sandbox; see issue #1). Graded blind together with the folder v2 run: grading-2/.
