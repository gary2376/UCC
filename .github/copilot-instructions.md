Always respond in 繁體中文

## When write code and modify files

### All languages

- DO NOT create a class if it is not necessary. Focus on FP. OOP is still ok, but in rare cases.
- Make minimal changes to files - modify only what's necessary to complete the task:
  - Focus on the specific task at hand, avoid unrelated improvements
  - Preserve existing code structure and formatting
  - Make changes in small, verifiable steps
  - Choose solutions that require minimal code changes
  - If needed, write in chat why minimal changes were not possible if larger changes are required and ask for approval
- Follow core software development principles:
  - TDD (Test-Driven Development): Write tests first, then implement the functionality
  - DRY (Don't Repeat Yourself): Avoid code duplication, extract reusable components
  - KISS (Keep It Simple, Stupid): Choose simple solutions over complex ones
  - YAGNI (You Aren't Gonna Need It): Don't implement functionality until it's necessary

### When writing in Python:

- Use Python with strict types for each variable
- Write down types of function results like `-> ...`
- Use Pydantic models for data structures instead of TypedDict or other solutions
- Try to avoid type Any
- Do not use @staticmethod
- Always prefer functional programming over OOP when possible.
- Use pyproject.toml instead of `requirements.txt`.
- When you mention a variable for the first time, try to write down the type. For example, scopes: list[str] = [...] (`: list[str]` added).

### When writing in other languages:

- Use strict types.
- Use clean functions. No hidden changes. No in-place changes.
- Follow all linter rules.
- Follow best practices.

## Libraries

- I install all Python packages in a virtual environment in the repo. Not to the whole system.
- Install libraries not 1 time. For example, not `pip install`, but add it to our project settings (`pyproject.toml`), and then run install by project script. And then `pip install -e ".[dev]"`.
- Don't hesitate to read library's source code instead of googling (use terminal commands like `pip show`, code $(pip show package | grep Location) to find and explore the code)

## Terminal

- Start all terminal commands with the pwd command as a separate call to be sure where you are.
- If the task is in any way related to the current date, for example, if you need to specify the current date in a filename or something else, then please execute the date command in the terminal to find out the current date first, and only then proceed with the task.
- Use GitHub CLI (`gh`) for all GitHub operations instead of web interface
- For multiline text in git/GitHub commands, use `printf`:
  git commit -m "$(printf "feat: Main change\n\n- Detail 1\n- Detail 2")"
  gh pr create --title "feat: New feature" --body "$(printf "- First point\n- Second point")"
  - Works for commits, PRs, issues, tags, etc.
  - Supports Markdown formatting
  - Works for gh commands as well

## Repository Best Practices

- Always start by reading README.md in the root - it's your primary source for project context, structure, and setup
- Pay special attention to README if .cursorrules is not present
- Summarize key points about the project before starting any work
