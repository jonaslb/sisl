from collections import deque
from functools import lru_cache


__all__ = ['Mixer', 'History', 'Metric']


class Mixer:
    r""" Base class mixer """

    def clear(self):
        r""" Dummy for history mixers such that all mixers can call `clear` """
        pass


class Metric:
    r""" Perform inner products using a metric

    An inner product can be defined as:

    .. math::

        s = \langle \mathbf a | \mathbf M | \mathbf b \rangle

    where generally the metric :math:`\mathbf M = 1`.
    """
    def __init__(self, metric=None):
        if metric is None:
            class _dummy_dot:
                def __call__(self, a):
                    return a
            self._metric = _dummy_dot()
        else:
            self._metric = metric

    def inner(self, a, b):
        r""" Perform the inner product between `a` and `b`

        Parameters
        ----------
        a, b: object
        """
        try:
            return a.dot(self._metric(b))
        except:
            return (a * self._metric(b)).sum()


class History:
    r""" A history class for retaining a set of history elements
    
    A history class may contain several different variables in a `collections.deque`
    list allowing easy managing of the length of the history.

    Attributes
    ----------
    variables : int
       number of different variables stored as a history
    history_max : int or tuple of int
       maximum number of history elements

    Parameters
    ----------
    history : int, optional
       number of maximum history elements stored
    variables : int, optional
       number of different variables stored as a history.
    """
    def __init__(self, history=2, variables=2):
        # Create a list of queues
        self._hist = [deque(maxlen=history) for i in range(variables)]

    @property
    @lru_cache(maxsize=1)
    def variables(self):
        r""" Number of different variables that can be contained """
        return len(self._hist)
        
    @property
    @lru_cache(maxsize=1)
    def history_max(self):
        r""" Maximum number of elements stored in the history for each variable """
        return self._hist[0].maxlen

    @property
    def history(self):
        r""" Number of elements in the history """
        return len(self._hist[0])

    __len__ = history

    def append(self, *args, variables=None):
        r""" Add variables to the history

        Parameters
        ----------
        *args : tuple of object
            each variable will be added to the history of the mixer
        variables : int or listlike of int
            specify which variables the history should be added to, note:
            ``len(args) == len(variables)``
        """
        if variables is None:
            variables = range(self.variables)

        # Clarify a few things
        variables = list(variables)
        if len(args) != len(variables):
            raise ValueError(f"{self.__class__.__name__}.append requires same length input")

        for i, arg in zip(variables, args):
            self._hist[i].append(arg)

    def clear(self, index=None, variables=None):
        r""" Clear variables to the history

        Parameters
        ----------
        index : int or array_like of int
            which indices of the history we should clear
        variables : int or array_like of int
            specify which variables should be cleared
        """
        if variables is None:
            variables = range(self.variables)
        variables = list(variables)

        if index is None:
            for v in variables:
                self._hist[v].clear()
        else:
            index = list(index)
            # We need to ensure we delete in the correct order
            index.sort(reverse=True)
            for v in variables:
                for i in index:
                    del self._hist[v][i]
