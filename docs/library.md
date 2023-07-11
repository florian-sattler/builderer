# Usage as library

Builderer can easily be used without configuration files.

## Example

The following example pipeline

```python
from builderer import Builderer, ActionFactory

f = ActionFactory(registry="registry.example.com", prefix="project/name")
b = Builderer(simulate=True)

b.add_action_likes(*f.build_image("frontend"))
b.add_action_likes(*f.build_image("backend"))
b.add_action_likes(*f.build_image("database"))

b.run()
```

will print

```
Building image: frontend
Building image: backend
Building image: database
Pushing image: database
Pushing image: backend
Pushing image: frontend
```

Note that because `simulate=True` was passed, no commands got issued.

!!! TIP "Hint"

    Pass `verbose=true` to see which commands would have been issued.

## Reference

::: builderer.actions
::: builderer.builderer
