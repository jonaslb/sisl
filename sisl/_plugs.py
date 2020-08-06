"""
# Plugs
This is maybe what was the idea with Nick's "attrs event handling" issue on sisl github?

Plugs are classes/objects: they contain both information eg names or additional atomic info for a geometry.
But they also contain hooks for geometry mutation operations to allow mutated geometries to have meaningfully transferred properties.
If a plug doesn't have any hooks for a geometry mutation, it is deleted in the mutation (to be implemented..)

The idea is to allow "Plugs"/hooks for Geometry mutation operations.
Eg. a possible base for _NamedIndex or Atoms or AnchorPoints (doesn't exist, but could be a user thing) etc for geometries.
Such that eg. `geom.mutate` doesn't have to do the mutation and then also do the work on all attached attributes.
Instead the attached attributes (plugs) register pre/post hooks on mutation method names.
They are then themselves responsible for doing the mutation in the relevant way for themselves.

Currently plugs can't be added to geometries because the mixin needs to be added.
Also plugs need to be explicitly added to the geom._plugs. Maybe a 'register' can be added to dynamically add plugs when user tries to access it.
But hooks should work.

Hooks must use the same call signature as the function they are hooking on to. They ALWAYS work in-place on the given geometry.
They shouldn't modify the arguments but can modify the geometry any way they see fit.
They shouldn't modify other Plugs because a Plug can't "want" to be run before each other.

Currently todo:
* Delete a plug if it doesnt have any hooks for a mutation (or doesn't mark it as donothing?)
* Write example Plug(s) to reveal any shortcomings of PlugsMixin
    * Eg. a `AnchorPoints` Plug to allow attaching geometries by matching anchor points
* Consider further functionality eg. getattr passthrough or getitem/index extensions
    * Could/should eventually turn geom.atoms and geom.names (at least this one) into Plugs
* Possibly context manager or clever kwargs parsing for changing Plug mutation behaviour
    * Eg. what to do with anchors when tiling: Keep anchor in first cell? Make tiled anchors in every cell or only edge cells? And what order then? Etc etc
* Probably more

"""
import inspect
from functools import wraps


class PlugsMixin:
    def __init__(self, *args, **kwargs):
        self._plugs = dict()

    def __getattr__(self, name):
        try:
            return self._plugs[name]
        except KeyError:
            raise AttributeError

    def __setattr__(self, name, value):
        if name in self._plugs:
            raise AttributeError(f"Can't set attribute {name!r} on {self!r} because a plug has that name.")
        super().__setattr__(name, value)

    def __getattribute__(self, name):
        attr = super().__getattribute__(name)

        if not callable(attr):
            return attr

        pre_funcs = []
        post_funcs = []
        
        for name, plug in self._plugs.items():
            try:
                pre_funcs.append(plug.pre_hooks[name])
            except KeyError:
                pass
            try:
                post_funcs.append(plug.post_hooks[name])
            except KeyError:
                pass
        
        if not pre_funcs and not post_funcs:
            return attr
        
        @wraps(attr)
        def combi_hook(obj, *args, **kwargs):
            inplace = False
            if "inplace" in kwargs:
                inplace = kwargs["inplace"]
            else:
                spec = inspect.getfullargspec(attr)
                if "inplace" in spec.args or "inplace" in spec.kwonlyargs:
                    # This can be trouble if the user uses kwargs positionally
                    kwargs["inplace"] = True
            if not inplace:
                obj = obj.copy()
            
            for f in pre_funcs:
                obj = f(obj, *args, **kwargs)
            obj = attr(obj, *args, **kwargs)
            for f in reversed(post_funcs):
                obj = f(obj, *args, **kwargs)
            return obj
        return combi_hook
        
