# arXiv submission checklist (human author)

Complete every item before uploading. Agents cannot check these for you.

## Content & integrity

- [ ] Every empirical number in `main.tex` matches my own experiments or is clearly marked TODO/hypothetical
- [ ] I personally verified every proof step in `appendix_math.tex`
- [ ] Every `\cite{}` key exists and I have read the cited work
- [ ] `verification_log.md` has no unresolved `TODO` for claims still in the paper
- [ ] Abstract accurately reflects contributions (no overclaiming)

## LaTeX & files

- [ ] `pdflatex` / `latexmk` builds `main.tex` without errors locally
- [ ] No disallowed or fragile packages (see arXiv TeX help)
- [ ] Figures exist at stated paths and are publication-quality

## arXiv metadata

- [ ] Primary category matches `arxiv_metadata.md`
- [ ] Title & abstract copied correctly into arXiv submission form
- [ ] Author list and affiliations correct
- [ ] License selected (default vs alternative understood)

## Policy

- [ ] I have rights to submit this work
- [ ] Not under conflicting journal embargo without checking journal rules
- [ ] AI assistance disclosed if required by institution/journal

## Post-upload

- [ ] Save arXiv ID and update `main.tex` comment `% arXiv:YYMM.NNNNN`
