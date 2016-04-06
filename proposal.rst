
Proposal: Making path objects inherit from ``str``.
===================================================

Abstract
--------

This proposal addresses issues that limit the usability of the
object-oriented filesystem path objects, most notably those of
``pathlib``, introduced in the standard library in Python 3.4 via PEP
0428. One issue being that the path objects are not directly compatible
with nearly any libraries, including the standard library. A further
goal of this proposal is to provide a smooth transition into a Python
with better Path handling, while keeping backwards compatiblity concerns
to a minimum. The approach involves making the path classes in
``pathlib`` (and optionally also DirEntry) subclasses of ``str``, but
takes further measures to avoid problems and unnecessary additions.

Introduction
------------

Filesystem paths are strings that give instructions for traversing a
directory tree. In Python, they have traditionally been represented as
byte strings, and more recently, unicode string. However, Python now has
``pathlib`` in the standard library, which is an object-oriented library
for dealing with objects specialized in representing a path and working
with it. In this proposal, such objects are generally referred to as
*path objects*, or sometimes, in the specific context of instances of
the ``pathlib`` path classes, they are explicitly referred to as
``pathlib`` objects.

In ``pathlib`` there is a hierarchy of path classes with a common base
class ``PurePath``. It has a subclass ``Path`` which essentially assumes
the path is intended to represent a path on the current system. However,
both of these classes, when called, instantiate a subclass of the
``Windows`` or ``Posix`` flavor, which have slightly different behavior.
In total, there are thus five public classes: ``PurePath``,
``PurePosixPath``, ``PureWindowsPath``, ``Path``, ``PosixPath`` and
``WindowsPath``.

Since Python 3.5 and the introduction of ``os.scandir``, the family of
path classes has a new member, ``DirEntry``, which is a
performance-oriented path object with significant duck-typing
compatibility with ``pathlib`` objects.

The adoption of the different types of path objects is still quite low,
which is perhaps unsurprising, because they were only introduced very
recently. However, it can also be inconvenient to work with these
objects, because, they usually need to be explicitly converted into
strings before passing them to functions, and path strings returned by
functions need to be explicitly converted into path objects. Especially
the latter issue is difficult in terms of backwards compatibility of
APIs. While many things were recently discussed on Python ideas
regarding the future of path-like objects, this proposal has a much more
limited scope, to provide first steps in the right direction. However,
the last part of this proposal considers possible future directions that
this may optionally lead to.

Rationale
---------

Filesystem paths (or comparable things like URIs) are strings of
characters that represent information needed to access a file or
directory (or other resource). In other words, they form a subset of
strings, involving specialized functionality such as joining absolute
and relative paths together, accessing different parts of the path or
file name, and even accessing the resources the path points to. In
Python terms, for a path ``path``, one would have
``isinstance(path, str)``. It is also clear that not all strings are
paths.

On the one hand, this would make an ideal case for making all
path-representing objects inherit from ``str``; while Python tries not
to over-emphasize object-oriented programming and inheritance, it should
not try to avoid class hierarchies when they are appropriate in terms of
both purity and practicality. Regarding practicality, making specialized
*path objects* also instances of ``str`` would make almost any stdlib or
third-party function accept path objects as path arguments, assuming
that they accept any instance of ``str``. Furthermore, functions now
returning instances of ``str`` to represent paths could in future
versions return path objects, with only minor backwards-incompatibility
worries.

On the other hand, strings are a very general concept, and the Python
``str`` class provides a large variety of methods to manipulate and work
with them, including ``.split()``, ``.find()``, ``.isnumeric()`` and
``.join()``. These operations may be defined just as well for a string
that represents a path than for any other string. In fact, this is the
status quo in Python, as the adoption of ``pathlib`` is still quite
limited and paths are in most cases represented as strings (sometimes
byte strings). But while the string operations are *defined* on
path-representing strings, the results of these operations may not be of
any use in most cases, even if in some cases, they may be.

While it is not the responsibility of the programming language to
prevent doing things that are not useful, it may be practical in some
cases. For instance, the string method ``.find()`` could be mistaken to
mean finding files on the file system, while it in fact searches for a
substring. String concatenation, in turn, can be a perfectly reasonable
thing to do: ``show_msg("Data saved to file: " + file_path)``. The
result of the concatenation of a string and a path is not a path, but a
general string. Directly concatenating two path objects together as
strings, however, likely has no sensible use cases.

There is prior art in subclassing the Python ``str`` type to build a
path object type. Packages on PyPI (TODO: list more?) that do this
include ``path.py`` and ``antipathy``. The latter also supports
``bytes``-based paths by instantiating a different class, a subclass of
``bytes``. Since these libraries have existed for several years,
experience from them is available for evaluating the potential benefits
and weaknesses of this proposal (as well as other aspects regarding
``pathlib``). However, this proposal goes a step further to avoid
potential problems and to provide a smooth transition plan that, if
desired, can be followed to painlessly move towards a Python with a
clear distinction between strings and paths. An optional long-term goal
that this proposal facilitates may be to gradually move away from using
strings (or even their subclasses) as paths.

Specification of standard library changes
-----------------------------------------

Making ``pathlib`` classes subclasses of ``str``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Assuming the present class hierarchy in ``pathlib``, inheritance from
``str`` will be introduced by making the base class ``pathlib.PurePath``
a subclass of ``str``. Methods will further be overridden in
``PurePath`` as described in the following.

Overriding all ``str``-specific methods
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Since most of the ``str`` methods are not of any use on paths and can be
confusing, leading to undesired behavior, *most* ``str`` methods
(including magic methods, but excluding methods listed below) are
overridden in ``PurePath`` with methods that by default raise
``TypeError("str method '<name>' is not available for paths."``. This
will help programmers to immediately notice when they are using the
wrong method. The perhaps unusual practice of disabling most base-class
methods can be regarded as being conservative in adding ``str``
functionality to path objects.

All methods, including double-underscore methods are overridden, except
for the following, which are *not* overridden:

-  Methods of the ``str`` or ``object`` types that are already
   overridden by ``PurePath``
-  Methods of the ``object`` type that are not overridden by ``str``
-  ``__getattribute__``
-  ``__len__`` (this could be debated, but not having it might be weird
   for a str instance)
-  ``encode``
-  ``startswith`` and ``endswith`` (TODO: override these with
   case-insensitive behavior on the windows flavor)
-  ``__add__`` will be overriden separately, as described in later
   subsections.

This will allow ``open(...)`` as well as most ``os`` and ``os.path``
functionality to work immediately, although there are cases that need
special handling.

Later, if shown to be desirable, some additional string methods may be
enabled on paths.

Overriding ``.__add__`` to disable adding two path objects together
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Overloading of the ``+`` operator in ``str`` will be overridden with a
version which disables concatenation of two path objects together while
allowing other type combinations (TODO: consider also fully disabling
+):

.. code:: python

    def __add__(self, other):
        if isinstance(other, PurePath):
            raise TypeError("Operator + for two paths is not defined; use / for joining paths.")
        return str.__add__(self, other)

Optional enabling of string methods
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Since many APIs currently have functions or methods that return paths as
strings, existing code may expect to have all string functionality
available on the returned objects. While most users are unlikely to use
much of the ``str`` functionality, a library function may want to
explicitly allow these operations on a path object that it returns.
Therefore, the overridden ``str`` methods can be enabled by setting a
``._enable_str_functionality`` method on a path object as follows:

-  ``pathobj._enable_str_functionality = True    #`` -- Enable ``str``
   methods
-  ``pathobj._enable_str_functionality = 'warn'  #`` -- Enable ``str``
   methods, but emit a ``FutureWarning`` with the message
   ``"str method '<name>' may be disabled on paths in future versions."``

The warning will help the API users notice that the return value is no
longer a plain path.

.. code:: python

    def <name>(self, *args, **kwargs):
        """Method of str, not for use with pathlib path objects."""
        try:
            enable = self._enable_str_functionality
        except AttributeError:
            raise TypeError("str method '{}' is not available for paths."
                                .format('<name>')) from None
        if enable == 'warn':
            warnings.warn("str method '{}' may be disabled on paths in future versions."
                              .format('<name>'), FutureWarning, stacklevel = 2)
        elif enable is True:
            pass
        else:
            raise ValueError("_enable_str_functionality can be True or 'warn'")
        return getattr(str, name)(self, *args, **kwargs)

New APIs, however, do not need to enable ``str`` functionality and may
return default path objects.

Helping interactive python tools and IDEs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Interactive Python tools such as Jupyter are growing in popularity. When
they use ``dir(...)`` to give suggestions for code completion, it is
harmful to have all the disabled ``str`` methods show up in the list,
even if they typically would raise exceptions. Therefore, the
``__dir__`` method should be overridden on ``PurePath`` to only show the
methods that are meaningful for paths. Some tools used for code
completion, such as ``rope`` and ``jedi`` may need some changes for
optimal code completion. This in fact includes also the standard Python
REPL, which currently does not respect ``__dir__`` in tab completion.

Changes needed to other stdlib modules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In stdlib modules other than ``pathlib``, mainly ``os``, ``ntpath`` and
``posixpath``, The stdlib functions in modules that use the
methods/functionality listed below on path or file names, will be
modified to explicitly convert the name ``name`` to a plain string
first, e.g., using ``getattr(name, 'path', name)``, which also works for
``DirEntry`` but may return ``bytes``:

-  ``split``
-  ``find``
-  ``rfind``
-  ``partition``
-  ``__iter__``
-  ``__getitem__``

(However, if ``DirEntry`` is not made to subclass ``str``, the idiom
``getattr(name, 'path', name)`` which is already supported in the
development version, should be implemented in stdlib functions to accept
not only ``str`` and path objects, but also DirEntry.)

Guidelines for third-party package maintainers
----------------------------------------------

Libraries that take paths as arguments or return them
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Since all of the standard library will accept path objects as path
arguments, most third-party libraries will automatically do so. However,
those that directly manipulate or examine the path name using ``str``
methods may not work. Those libraries will not immediately be
``pathlib``-compatible.

To achieve full ``pathlib``-compatiblity, the libraries are advised to:
1. Make sure they do not explicitly check the ``type(...)`` of
arguments, but use ``isinstance(...)`` instead, if needed. 2. See if
their functions use disabled ``str``/``bytes`` methods on paths that
they take as arguments. If so, they should either: \* change their code
to, achieve the same using ``os.path`` functions (*this is the preferred
option*), or \* convert the argument first using
``name = getattr(name, 'path', name)``, which does not require importing
pathlib 3. Consider, when returning a path or file name, to convert it
to a path object first if a ``str``-subclassing ``pathlib`` is
available. During a transition period, the attribute
``._enable_str_functionality = 'warn'`` should be set before returning
the object. For an even softer, transition period it is also possible to
set ``._enable_str_functionality = True``, which enables ``str`` methods
with no warnings.

Pathlib-compatible or near-compatible libraries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To have the best level of compatibility, all path-like objects should
preferably behave similarly to pathlib objects regarding subclassing
``str``. However, for the best level of *compatibility*, the safest
options is to subclass ``str`` and *not* disable ``str`` functionality
(which is already done by some known libraries). However, they may want
to further disable methods of ``str`` to achieve the additional clarity
that ``pathlib`` has regarding \* Having a ``.path`` attribute/property
which gives a ``str`` (or ``bytes``) instance representing the path

Older Python versions
~~~~~~~~~~~~~~~~~~~~~

The ``pathlib2`` module, which provides ``pathlib`` to pre-3.4 python
versions, can also subclass ``str``, but it should by default have
``._enable_str_functionality = 'warn'`` or
``.enable_str_functionality = True``, because the stdlib in the older
Python-versions is not compatible with paths that have ``str``
functionality disabled.

Transition plans and future possibilities for long-term consideration
---------------------------------------------------------------------

``DirEntry``
~~~~~~~~~~~~

``DirEntry`` should also undergo a similar transition, which was, at
first, part of this proposal, but it was removed to limit the scope (It
could be added back, of course, if desired). Since ``DirEntry`` focuses
on performance, it is important not to cause any significant performance
drops.

It would, however, simplify things if ``DirEntry`` did the same as
``pathlib`` regarding subclassing and disabling methods. A slight
complication, however, arises from the fact that ``DirEntry`` may
represent a path using ``bytes``, making the ``.path`` attribute also an
instance of ``bytes`` instead of ``str``. This issue could be solved by
at least two different approaches:

1. Make ``bytes``-kind DirEntry instances, interpreted as ``str``
   instances, equivalent to ``os.fsdecode(direntry.path)``.
2. Instantiate a different ``DirEntry`` class for ``bytes`` paths,
   perhaps in a way similar to how the ``antipathy`` path library
   instantiates ``bPath`` when the ``bytes`` type is used.

The future of plain string paths and ``os.path``?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is possible to imagine having both ``os.path`` and ``pathlib``
coexist, as long as they co-operate well. Potentially, things like
``open("filename.txt")`` with a plain string argument will always be
accepted. However, if regardless of what people use Python for, they
slowly adopt path objects as the way to represent a path, the support
for plain string paths may be deprecated and eventually dropped.

On the one hand, to support the former situation, ``os.path`` functions
can choose their return type to match the type of the arguments; with
multiple different types in the arguments, ``pathlib`` might 'win'
because it is already imported. On the other hand, to support the
latter, all path-returning functions in the stdlib can begin to return
pathlib objects, at first with ``str`` methods enabled with or without
warning, and eventually, with ``str`` methods disabled.

Literal syntax for paths: p-strings?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Should Python choose the *path* towards not allowing plain strings as
paths, a convenient way to instantiate a path is desperately needed. As
discussed in the recent python-ideas thread "Working with path objects:
p-strings?", one possibility would be a new syntax like
``p"/path/to/file.ext"``, which would instantiate a path object.

Another way of turning a string into a path could be to have a ``.path``
property on ``str`` objects that instantiates and returns a path object.
It can be debated whether this 'Pythonic' or not. See also the next
section.

The ``.path`` attribute on path-like objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``DirEntry`` already had the ``.path`` attribute when it was introduced
to the standard library in Python 3.5. It represents the absolute or
relative path as a whole as a ``str`` or ``bytes`` instance. However,
several people have raised the concern that the word ``path`` not
referring to an actual path object may be misleading. However, if path
objects are instances of str, the ``.path`` may in the future shift to
mean the path object. In the case of ``pathlib`` paths, it would could
be implemented as a property that returns ``self``, or during a
transition phase, a path object with ``str`` functions enabled:

.. code:: python

        @property
        def path(self):
            path = type(self)(self)
            path._enable_str_functionality = 'warn'
            return self

``DirEntry`` objects, on the other hand, could be converted to pathlib
objects using the ``.path`` method. Similarly, ``str`` objects could
have a similar property for conversion into a pathlib object (see
previous section).

Possibilities for making ``pathlib`` more lightweight
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If path objects were to become the norm in handling paths and file
names, there may be a need for optimizations in terms of the speed and
memory usage of path objects as well as the import time and memory
footprint. Dependencies that are not always used by pathlib objects
could also be imported lazily.

Another base class for path-like objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Python already has multiple types that can represent paths-like objects.
There could be one common base class for all of them, which would (at
least at first) inherit from ``str``. ``DirEntry`` and ``PurePath``
would both be subclasses of this class.

One would, however, need to answer the questions of what this class
would be called, what it would look like, and what module would it be in
(if not builtin). For now, let us call it ``PyRL`` for Python
(Pyniversal?-) Resource Locator. This could also be a base class for
URLs/URIs.

Generalized Resource Locator addresses: a-strings? l-strings?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

... not to mention g-strings!

A generalized concept may be valuable in the future, because the
distinction between local and remote is getting more and more vague. As
discussed in the python-ideas thread "URLs/URIs + pathlib.Path + literal
syntax = ?", it is possible to quite reliably distinguish common types
of URLs from filesystem paths. If this became the norm, many
Python-written programs could 'magically' accept URLs as input file
paths by simply calling the ``PyRL(...)``, which could be equivalent to
some literal syntax for use in a scripting, testing or interactive
setting, or when loading config files from fixed locations.

