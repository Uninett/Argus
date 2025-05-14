## Scope and purpose

Fixes #<!-- ISSUE-ID -->. Dependent on #<!-- PULL-REQUEST-ID -->. <!-- Reference: https://docs.github.com/en/issues/tracking-your-work-with-issues/linking-a-pull-request-to-an-issue -->

Add a description of what this PR does and why it is needed. If a linked ticket(s) fully
cover it, you can omit this.

<!-- remove things that do not apply -->
### This pull request
* adds/changes/removes a dependency
* changes the database
* changes the API <!-- Ensure that v2 is backwards compatible, v3 can be changing things -->


## Contributor Checklist

Every pull request should have this checklist filled out, no matter how small it is.
More information about contributing to Argus can be found in the
[Development docs](https://argus-server.readthedocs.io/en/latest/development.html).

<!-- Add an "X" inside the brackets to confirm -->
<!-- Remove checks that do not apply -->
<!-- Of the checks that do apply: If not checking one or more of the boxes, please explain why below each. -->

* [ ] Added a changelog fragment for [towncrier](https://argus-server.readthedocs.io/en/latest/development/howtos/changelog-entry.html)
* [ ] Added/amended tests for new/changed code
* [ ] Added/changed documentation
* [ ] Linted/formatted the code with ruff and djLint, easiest by using [pre-commit](https://github.com/Uninett/Argus?tab=readme-ov-file#code-style)
* [ ] The first line of the commit message continues the sentence "If applied, this commit will ...", starts with a capital letter, does not end with punctuation and is 50 characters or less long. See our [how-to](https://argus-server.readthedocs.io/en/latest/development/howtos/commit-messages.html)
* [ ] If applicable: Created new issues if this PR does not fix the issue completely/there is further work to be done
* [ ] If this results in changes in the UI: Added screenshots of the before and after
* [ ] If this results in changes to the database model: Updated the [ER diagram](https://argus-server.readthedocs.io/en/latest/development/howtos/regenerate-the-ER-diagram.html)

<!-- Make this a draft PR if the content is subject to change, cannot be merged or if it is for initial feedback -->
