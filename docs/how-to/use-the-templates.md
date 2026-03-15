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

## Start from the Python and Node template

1. Copy `templates/python-node-secure` into your new repository.
2. Update the package metadata in `pyproject.toml` and `package.json`.
3. Rename the Python package under `backend/src/`.
4. Replace the TypeScript sample module under `frontend/src/`.
5. Reopen the repository in a devcontainer.
6. Run `task ci`.

## Start from the Java template

1. Copy `templates/java-secure` into your new repository.
2. Update the project name in `settings.gradle.kts`.
3. Replace the sample sources under `src/main/java/` and `src/test/java/`.
4. Reopen the repository in a devcontainer.
5. Run `task ci`.

If you want to use the published Java image directly instead of copying the
template Containerfile, follow [Use the Published Java Image](./use-the-published-java-image.md).

## Keep the contract unchanged

Do not rename the required tasks:

- `task init`
- `task lint`
- `task test`
- `task scan`
- `task ci`
