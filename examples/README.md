# Examples

The `examples/` directory provides documented workspaces that teach the
validated environments and implemented features in this repository.

Use these when you want to learn by opening a working environment in VS Code or
by having an agent operate against a prewired workspace.

## Available examples

- [python-example](./python-example/README.md): the smallest repository-owned
  Python reference path
- [python-image-example](./python-image-example/README.md): consume the
  published Python and Node image directly for Python work
- [python-maintenance-example](./python-maintenance-example/README.md): richer
  Python dependency-maintenance fixture
- [diagram-image-example](./diagram-image-example/README.md): consume the
  published diagrams image directly for CVE presentation visuals
- [java-image-example](./java-image-example/README.md): consume the published
  Java image directly for Java work
- [java-maintenance-example](./java-maintenance-example/README.md): richer Java
  dependency-maintenance fixture

## Standard workflow

1. Open an example in VS Code.
2. Reopen it in the devcontainer.
3. Wait for `postCreateCommand` to finish.
4. Start with `man polyglot`.
5. Run `task ci` unless you are intentionally exploring dependency-maintenance
   flows.

## Templates versus examples

Use `templates/` when you want a starter repository to copy into a new
project.

Use `examples/` when you want a working, documented environment that shows how
the images, templates, runtime docs, and task contract behave in practice.
