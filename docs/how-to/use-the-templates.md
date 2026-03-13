# Use the Templates

## Start from the Python template

1. Copy `templates/python-secure` into your new repository.
2. Update the package name in `pyproject.toml`.
3. Rename `src/python_secure_template`.
4. Reopen the repository in a devcontainer.
5. Run `task ci`.

## Start from the Node template

1. Copy `templates/node-secure` into your new repository.
2. Update `package.json` name and description fields.
3. Replace the sample module in `src/`.
4. Reopen the repository in a devcontainer.
5. Run `task ci`.

## Keep the contract unchanged

Do not rename the required tasks:

- `task init`
- `task lint`
- `task test`
- `task scan`
- `task ci`
