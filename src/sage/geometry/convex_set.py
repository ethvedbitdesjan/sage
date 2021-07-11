r"""
Convex Sets
"""

# ****************************************************************************
#       Copyright (C) 2021 Matthias Koeppe
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#                  https://www.gnu.org/licenses/
# ****************************************************************************

from dataclasses import dataclass
from typing import Any
from copy import copy

from sage.structure.sage_object import SageObject
from sage.misc.abstract_method import abstract_method
from sage.misc.cachefunc import cached_method
from sage.modules.free_module_element import vector
from sage.matrix.constructor import matrix


@dataclass
class AffineHullProjectionData:
    image: Any = None
    projection_linear_map: Any = None
    projection_translation: Any = None
    section_linear_map: Any = None
    section_translation: Any = None


class ConvexSet_base(SageObject):
    """
    Abstract base class for convex sets.
    """

    def is_empty(self):
        r"""
        Test whether ``self`` is the empty set.

        OUTPUT:

        Boolean.

        EXAMPLES::

            sage: p = LatticePolytope([], lattice=ToricLattice(3).dual()); p
            -1-d lattice polytope in 3-d lattice M
            sage: p.is_empty()
            True
        """
        return self.dim() < 0

    def is_universe(self):
        r"""
        Test whether ``self`` is the whole ambient space.

        OUTPUT:

        Boolean.

        TESTS::

            sage: from sage.geometry.convex_set import ConvexSet_base
            sage: C = ConvexSet_base()
            sage: C.is_universe()
            Traceback (most recent call last):
            ...
            NotImplementedError
        """
        if not self.is_full_dimensional():
            return False
        raise NotImplementedError

    def dim(self):
        r"""
        Return the dimension of ``self``.

        Subclasses must provide an implementation of this method or of the
        method :meth:`an_affine_basis`.

        TESTS::

            sage: from sage.geometry.convex_set import ConvexSet_base
            sage: C = ConvexSet_base()
            sage: C.dim()
            Traceback (most recent call last):
            ...
            NotImplementedError
        """
        if self.an_affine_basis != NotImplemented:
            return len(self.an_affine_basis()) - 1
        raise NotImplementedError

    def dimension(self):
        r"""
        Return the dimension of ``self``.

        This is the same as :meth:`dim`.

        EXAMPLES::

            sage: from sage.geometry.convex_set import ConvexSet_base
            sage: class ExampleSet(ConvexSet_base):
            ....:     def dim(self):
            ....:         return 42
            sage: ExampleSet().dimension()
            42
        """
        return self.dim()

    @abstract_method
    def ambient_vector_space(self, base_field=None):
        r"""
        Return the ambient vector space.

        Subclasses must provide an implementation of this method.

        The default implementations of :meth:`ambient`, :meth:`ambient_dim`,
        :meth:`ambient_dimension` use this method.

        EXAMPLES::

            sage: from sage.geometry.convex_set import ConvexSet_base
            sage: C = ConvexSet_base()
            sage: C.ambient_vector_space()
            Traceback (most recent call last):
            ...
            NotImplementedError: <abstract method ambient_vector_space at ...>
        """

    def ambient(self):
        r"""
        Return the ambient convex set or space.

        The default implementation delegates to :meth:`ambient_vector_space`.

        EXAMPLES::

            sage: from sage.geometry.convex_set import ConvexSet_base
            sage: class ExampleSet(ConvexSet_base):
            ....:     def ambient_vector_space(self, base_field=None):
            ....:         return (base_field or QQ)^2001
            sage: ExampleSet().ambient()
            Vector space of dimension 2001 over Rational Field
        """
        return self.ambient_vector_space()

    def ambient_dim(self):
        r"""
        Return the dimension of the ambient convex set or space.

        The default implementation obtains it from :meth:`ambient`.

        EXAMPLES::

            sage: from sage.geometry.convex_set import ConvexSet_base
            sage: class ExampleSet(ConvexSet_base):
            ....:     def ambient(self):
            ....:         return QQ^7
            sage: ExampleSet().ambient_dim()
            7
        """
        return self.ambient().dimension()

    def ambient_dimension(self):
        r"""
        Return the dimension of the ambient convex set or space.

        This is the same as :meth:`ambient_dim`.

        EXAMPLES::

            sage: from sage.geometry.convex_set import ConvexSet_base
            sage: class ExampleSet(ConvexSet_base):
            ....:     def ambient_dim(self):
            ....:         return 91
            sage: ExampleSet().ambient_dimension()
            91
        """
        return self.ambient_dim()

    @abstract_method(optional=True)
    def an_affine_basis(self):
        r"""
        Return points that form an affine basis for the affine hull.

        The points are guaranteed to lie in the topological closure of ``self``.

        EXAMPLES::

            sage: from sage.geometry.convex_set import ConvexSet_base
            sage: C = ConvexSet_base()
            sage: C.an_affine_basis()
            Traceback (most recent call last):
            ...
            TypeError: 'NotImplementedType' object is not callable
        """

    def _test_an_affine_basis(self, tester=None, **options):
        r"""
        Run tests on the method :meth:`.an_affine_basis`

        TESTS::

            sage: c = Cone([(1,0)])
            sage: c._test_an_affine_basis()
        """
        if tester is None:
            tester = self._tester(**options)
        try:
            if self.an_affine_basis == NotImplemented:
                raise NotImplementedError
            b = self.an_affine_basis()
        except NotImplementedError:
            pass
        else:
            m = matrix([1] + list(v) for v in b)
            tester.assertEqual(m.rank(), self.dim() + 1)
            closure = self.closure()
            for v in b:
                tester.assertIn(v, closure)

    def affine_hull(self, *args, **kwds):
        r"""
        Return the affine hull of ``self`` as a polyhedron.

        EXAMPLES::

            sage: from sage.geometry.convex_set import ConvexSet_compact
            sage: class EmbeddedDisk(ConvexSet_compact):
            ....:     def an_affine_basis(self):
            ....:         return [vector([1, 0, 0]), vector([1, 1, 0]), vector([1, 0, 1])]
            sage: O = EmbeddedDisk()
            sage: O.dim()
            2
            sage: O.affine_hull()
            A 2-dimensional polyhedron in QQ^3 defined as the convex hull of 1 vertex and 2 lines
        """
        from .polyhedron.constructor import Polyhedron
        i_affine_basis = iter(self.an_affine_basis())
        try:
            v = next(i_affine_basis)
        except StopIteration:
            return Polyhedron(ambient_dim=self.ambient_dim())
        v = vector(v)
        return Polyhedron(vertices=[v], lines=[vector(p) - v for p in i_affine_basis])

    @cached_method
    def _affine_hull_projection(self, *,
                                as_convex_set=True, as_affine_map=True, as_section_map=True,
                                orthogonal=False, orthonormal=False,
                                extend=False, minimal=False):
        r"""
        Return ``self`` projected into its affine hull.

        Each convex set is contained in some smallest affine subspace
        (possibly the entire ambient space) -- its affine hull.  We
        provide an affine linear map that projects the ambient space of
        the convex set to the standard Euclidean space of dimension of
        the convex set, which restricts to a bijection from the affine
        hull.

        The projection map is not unique; some parameters control the
        choice of the map.  Other parameters control the output of the
        function.

        This default implementation delegates to
        :meth:`~sage.geometry.polyhedron.base.Polyhedron_base._affine_hull_projection`,
        applied to the affine hull of ``self``.

        Subclasses should override this method if they can provide a
        more direct implementation or additional options.
        """
        affine_hull = self.affine_hull()
        data = affine_hull._affine_hull_projection(
            as_convex_set=False, as_affine_map=True, as_section_map=True,
            orthogonal=orthogonal, orthonormal=orthonormal,
            extend=extend, minimal=minimal)
        if as_convex_set:
            data = copy(data)
            matrix = data.projection_linear_map.matrix().transpose()
            projected = self.linear_transformation(matrix)
            data.image = projected.translation(data.projection_translation)
        return data

    def affine_hull_projection(self, as_convex_set=None, as_affine_map=False,
                               orthogonal=False, orthonormal=False,
                               extend=False, minimal=False,
                               return_all_data=False, **kwds):
        r"""
        Return ``self`` projected into its affine hull.

        Each convex set is contained in some smallest affine subspace
        (possibly the entire ambient space) -- its affine hull.  We
        provide an affine linear map that projects the ambient space of
        the convex set to the standard Euclidean space of dimension of
        the convex set, which restricts to a bijection from the affine
        hull.

        The projection map is not unique; some parameters control the
        choice of the map.  Other parameters control the output of the
        function.

        EXAMPLES::

            sage: P = Polyhedron(vertices=[[1, 0], [0, 1]])
            sage: ri_P = P.relative_interior(); ri_P
            Relative interior of a 1-dimensional polyhedron in ZZ^2 defined as the convex hull of 2 vertices
            sage: ri_P.affine_hull_projection(as_affine_map=True)
            (Vector space morphism represented by the matrix:
            [1]
            [0]
            Domain: Vector space of dimension 2 over Rational Field
            Codomain: Vector space of dimension 1 over Rational Field,
            (0))
            sage: P_aff = P.affine_hull_projection(); P_aff
            A 1-dimensional polyhedron in ZZ^1 defined as the convex hull of 2 vertices
            sage: ri_P_aff = ri_P.affine_hull_projection(); ri_P_aff
            Relative interior of a 1-dimensional polyhedron in QQ^1 defined as the convex hull of 2 vertices
            sage: ri_P_aff.closure() == P_aff
            True
         """
        if as_convex_set is None:
            as_convex_set = not as_affine_map
        if not as_affine_map and not as_convex_set:
            raise ValueError('combining "as_affine_map=False" and '
                             '"as_convex_set=False" not allowed')
        if return_all_data:
            as_convex_set = True
            as_affine_map = True

        result = self._affine_hull_projection(
            as_convex_set=as_convex_set, as_affine_map=as_affine_map, as_section_map=return_all_data,
            orthogonal=orthogonal, orthonormal=orthonormal,
            extend=extend, minimal=minimal, **kwds)

        # assemble result
        if return_all_data or (as_convex_set and as_affine_map):
            return result
        elif as_affine_map:
            return (result.projection_linear_map, result.projection_translation)
        else:
            return result.image

    def codimension(self):
        r"""
        Return the codimension of ``self`` in `self.ambient()``.

        EXAMPLES::

            sage: P = Polyhedron(vertices=[(1,2,3)], rays=[(1,0,0)])
            sage: P.codimension()
            2

        An alias is :meth:`codim`::

            sage: P.codim()
            2
        """
        return self.ambient_dim() - self.dim()

    codim = codimension

    def is_full_dimensional(self):
        r"""
        Return whether ``self`` is full dimensional.

        OUTPUT:

        Boolean. Whether the polyhedron is not contained in any strict
        affine subspace.

        EXAMPLES::

            sage: c = Cone([(1,0)])
            sage: c.is_full_dimensional()
            False

            sage: polytopes.hypercube(3).is_full_dimensional()
            True
            sage: Polyhedron(vertices=[(1,2,3)], rays=[(1,0,0)]).is_full_dimensional()
            False
        """
        return self.dim() == self.ambient_dim()

    def is_open(self):
        r"""
        Return whether ``self`` is open.

        The default implementation of this method only knows that the
        empty set and the ambient space are open.

        OUTPUT:

        Boolean.

        EXAMPLES::

            sage: from sage.geometry.convex_set import ConvexSet_base
            sage: class ExampleSet(ConvexSet_base):
            ....:     def is_empty(self):
            ....:         return False
            ....:     def is_universe(self):
            ....:         return True
            sage: ExampleSet().is_open()
            True
        """
        if self.is_empty() or self.is_universe():
            return True
        raise NotImplementedError

    def is_relatively_open(self):
        r"""
        Return whether ``self`` is relatively open.

        The default implementation of this method only knows that open
        sets are also relatively open, and in addition singletons are
        relatively open.

        OUTPUT:

        Boolean.

        EXAMPLES::

            sage: from sage.geometry.convex_set import ConvexSet_base
            sage: class ExampleSet(ConvexSet_base):
            ....:     def is_open(self):
            ....:         return True
            sage: ExampleSet().is_relatively_open()
            True
        """
        if self.is_open():
            return True
        if self.dim() == 0:
            return True
        raise NotImplementedError

    def is_closed(self):
        r"""
        Return whether ``self`` is closed.

        The default implementation of this method only knows that the
        empty set, a singleton set, and the ambient space are closed.

        OUTPUT:

        Boolean.

        EXAMPLES::

            sage: from sage.geometry.convex_set import ConvexSet_base
            sage: class ExampleSet(ConvexSet_base):
            ....:     def dim(self):
            ....:         return 0
            sage: ExampleSet().is_closed()
            True
        """
        if self.is_empty() or self.dim() == 0 or self.is_universe():
            return True
        raise NotImplementedError

    def is_compact(self):
        r"""
        Return whether ``self`` is compact.

        The default implementation of this method only knows that a
        non-closed set cannot be compact, and that the empty set and
        a singleton set are compact.

        OUTPUT:

        Boolean.

            sage: from sage.geometry.convex_set import ConvexSet_base
            sage: class ExampleSet(ConvexSet_base):
            ....:     def dim(self):
            ....:         return 0
            sage: ExampleSet().is_compact()
            True
        """
        if not self.is_closed():
            return False
        if self.dim() < 1:
            return True
        raise NotImplementedError

    def closure(self):
        r"""
        Return the topological closure of ``self``.

        EXAMPLES::

            sage: from sage.geometry.convex_set import ConvexSet_closed
            sage: C = ConvexSet_closed()
            sage: C.closure() is C
            True
        """
        if self.is_closed():
            return self
        raise NotImplementedError

    def interior(self):
        r"""
        Return the topological interior of ``self``.

        EXAMPLES::

            sage: from sage.geometry.convex_set import ConvexSet_open
            sage: C = ConvexSet_open()
            sage: C.interior() is C
            True
        """
        if self.is_open():
            return self
        raise NotImplementedError

    def relative_interior(self):
        r"""
        Return the relative interior of ``self``.

        EXAMPLES::

            sage: from sage.geometry.convex_set import ConvexSet_relatively_open
            sage: C = ConvexSet_relatively_open()
            sage: C.relative_interior() is C
            True
        """
        if self.is_relatively_open():
            return self
        raise NotImplementedError

    def _test_convex_set(self, tester=None, **options):
        """
        Run some tests on the methods of :class:`ConvexSet_base`.

        TESTS::

            sage: from sage.geometry.convex_set import ConvexSet_open
            sage: class FaultyConvexSet(ConvexSet_open):
            ....:     def ambient(self):
            ....:         return QQ^55
            ....:     def ambient_vector_space(self, base_field=None):
            ....:         return QQ^16
            ....:     def is_universe(self):
            ....:         return True
            ....:     def dim(self):
            ....:         return 42
            ....:     def ambient_dim(self):
            ....:         return 91
            sage: TestSuite(FaultyConvexSet()).run(skip=('_test_pickling', '_test_contains'))
            Failure in _test_convex_set:
            ...
            The following tests failed: _test_convex_set

            sage: class BiggerOnTheInside(ConvexSet_open):
            ....:     def dim(self):
            ....:         return 100000
            ....:     def ambient_vector_space(self):
            ....:         return QQ^3
            ....:     def ambient(self):
            ....:         return QQ^3
            ....:     def ambient_dim(self):
            ....:         return 3
            sage: TestSuite(BiggerOnTheInside()).run(skip=('_test_pickling', '_test_contains'))
            Failure in _test_convex_set:
            ...
            The following tests failed: _test_convex_set

        """
        if tester is None:
            tester = self._tester(**options)
        dim = self.dim()
        codim = self.codim()
        tester.assertTrue(dim <= self.ambient_dim())
        if dim >= 0:
            tester.assertTrue(dim + codim == self.ambient_dim())
        if self.is_empty():
            tester.assertTrue(dim == -1)
        if self.is_universe():
            tester.assertTrue(self.is_full_dimensional())
        cl_self = self.closure()
        try:
            int_self = self.interior()
        except NotImplementedError:
            int_self = None
        try:
            relint_self = self.relative_interior()
        except NotImplementedError:
            relint_self = None
        if self.is_full_dimensional():
            tester.assertTrue(int_self == relint_self)
        if self.is_relatively_open():
            tester.assertTrue(self == relint_self)
        if self.is_open():
            tester.assertTrue(self == int_self)
        if self.is_closed():
            tester.assertTrue(self == cl_self)
        if self.is_compact():
            tester.assertTrue(self.is_closed())
        from sage.misc.sage_unittest import TestSuite
        if relint_self is not None and relint_self is not self:
            tester.info("\n  Running the test suite of self.relative_interior()")
            TestSuite(relint_self).run(verbose=tester._verbose,
                                       prefix=tester._prefix + "  ")
            tester.info(tester._prefix + " ", newline=False)

    # Optional methods

    @abstract_method(optional=True)
    def cartesian_product(self, other):
        """
        Return the Cartesian product.

        INPUT:

        - ``other`` -- another convex set

        OUTPUT:

        The Cartesian product of ``self`` and ``other``.

        TESTS::

            sage: from sage.geometry.convex_set import ConvexSet_base
            sage: C = ConvexSet_base()
            sage: C.cartesian_product(C)
            Traceback (most recent call last):
            ...
            TypeError: 'NotImplementedType' object is not callable
        """

    @abstract_method(optional=True)
    def contains(self, point):
        """
        Test whether ``self`` contains the given ``point``.

        INPUT:

        - ``point`` -- a point or its coordinates

        TESTS::

            sage: from sage.geometry.convex_set import ConvexSet_base
            sage: C = ConvexSet_base()
            sage: C.contains(vector([0, 0]))
            Traceback (most recent call last):
            ...
            TypeError: 'NotImplementedType' object is not callable
        """

    def _test_contains(self, tester=None, **options):
        """
        Test the ``contains`` method.

        EXAMPLES::

            sage: from sage.geometry.convex_set import ConvexSet_closed
            sage: class FaultyConvexSet(ConvexSet_closed):
            ....:     def ambient_vector_space(self, base_field=QQ):
            ....:         return base_field^2
            ....:     ambient = ambient_vector_space
            ....:     def contains(self, point):
            ....:         if isinstance(point, (tuple, list)):
            ....:             return all(x in ZZ for x in point)
            ....:         return point.parent() == ZZ^2
            sage: FaultyConvexSet()._test_contains()
            Traceback (most recent call last):
            ...
            AssertionError: False != True

            sage: class AlsoFaultyConvexSet(ConvexSet_closed):
            ....:     def ambient_vector_space(self, base_field=QQ):
            ....:         return base_field^2
            ....:     def ambient(self):
            ....:         return ZZ^2
            ....:     def contains(self, point):
            ....:         return point in ZZ^2
            sage: AlsoFaultyConvexSet()._test_contains()
            Traceback (most recent call last):
            ...
            AssertionError: True != False
        """
        if tester is None:
            tester = self._tester(**options)
        ambient = self.ambient()
        space = self.ambient_vector_space()
        try:
            ambient_point = ambient.an_element()
        except (AttributeError, NotImplementedError):
            ambient_point = None
            space_point = space.an_element()
        else:
            space_point = space(ambient_point)
        space_coords = space.coordinates(space_point)
        if self.contains != NotImplemented:
            contains_space_point = self.contains(space_point)
            if ambient_point is not None:
                tester.assertEqual(contains_space_point, self.contains(ambient_point))
            tester.assertEqual(contains_space_point, self.contains(space_coords))
            if space.base_ring().is_exact():
                from sage.rings.qqbar import AA
                ext_space = self.ambient_vector_space(AA)
                ext_space_point = ext_space(space_point)
                tester.assertEqual(contains_space_point, self.contains(ext_space_point))
            from sage.symbolic.ring import SR
            symbolic_space = self.ambient_vector_space(SR)
            symbolic_space_point = symbolic_space(space_point)
            # Only test that it can accept SR vectors without error.
            self.contains(symbolic_space_point)

    @abstract_method(optional=True)
    def intersection(self, other):
        r"""
        Return the intersection of ``self`` and ``other``.

        INPUT:

        - ``other`` -- another convex set

        OUTPUT:

        The intersection.

        TESTS::

            sage: from sage.geometry.convex_set import ConvexSet_base
            sage: C = ConvexSet_base()
            sage: C.intersection(C)
            Traceback (most recent call last):
            ...
            TypeError: 'NotImplementedType' object is not callable
        """

    @abstract_method(optional=True)
    def dilation(self, scalar):
        """
        Return the dilated (uniformly stretched) set.

        INPUT:

        - ``scalar`` -- A scalar, not necessarily in :meth:`base_ring`
        """

    @abstract_method(optional=True)
    def linear_transformation(self, linear_transf, **kwds):
        """
        Return the linear transformation of ``self``.

        INPUT:

        - ``linear_transf`` -- a matrix
        - ``**kwds`` -- passed to the :meth:`linear_transformation` method of
          the closure of ``self``.
        """

    @abstract_method(optional=True)
    def translation(self, displacement):
        """
        Return the translation of ``self`` by a ``displacement`` vector.

        INPUT:

        - ``displacement`` -- a displacement vector or a list/tuple of
          coordinates that determines a displacement vector
        """


class ConvexSet_closed(ConvexSet_base):
    r"""
    Abstract base class for closed convex sets.
    """

    def is_closed(self):
        r"""
        Return whether ``self`` is closed.

        OUTPUT:

        Boolean.

        EXAMPLES::

            sage: hcube = polytopes.hypercube(5)
            sage: hcube.is_closed()
            True
        """
        return True

    def is_open(self):
        r"""
        Return whether ``self`` is open.

        OUTPUT:

        Boolean.

        EXAMPLES::

            sage: hcube = polytopes.hypercube(5)
            sage: hcube.is_open()
            False

            sage: zerocube = polytopes.hypercube(0)
            sage: zerocube.is_open()
            True
        """
        return self.is_empty() or self.is_universe()


class ConvexSet_compact(ConvexSet_closed):
    r"""
    Abstract base class for compact convex sets.
    """

    def is_universe(self):
        r"""
        Return whether ``self`` is the whole ambient space

        OUTPUT:

        Boolean.

        EXAMPLES::

            sage: cross3 = lattice_polytope.cross_polytope(3)
            sage: cross3.is_universe()
            False
            sage: point0 = LatticePolytope([[]]); point0
            0-d reflexive polytope in 0-d lattice M
            sage: point0.is_universe()
            True
        """
        return self.ambient_dim() == 0 and not self.is_empty()

    def is_compact(self):
        r"""
        Return whether ``self`` is compact.

        OUTPUT:

        Boolean.

        EXAMPLES::

            sage: cross3 = lattice_polytope.cross_polytope(3)
            sage: cross3.is_compact()
            True
        """
        return True

    is_relatively_open = ConvexSet_closed.is_open


class ConvexSet_relatively_open(ConvexSet_base):
    r"""
    Abstract base class for relatively open convex sets.
    """

    def is_relatively_open(self):
        r"""
        Return whether ``self`` is relatively open.

        OUTPUT:

        Boolean.

        EXAMPLES::

            sage: segment = Polyhedron([[1, 2], [3, 4]])
            sage: ri_segment = segment.relative_interior()
            sage: ri_segment.is_relatively_open()
            True
        """
        return True

    def is_open(self):
        r"""
        Return whether ``self`` is open.

        OUTPUT:

        Boolean.

        EXAMPLES::

            sage: segment = Polyhedron([[1, 2], [3, 4]])
            sage: ri_segment = segment.relative_interior()
            sage: ri_segment.is_open()
            False
        """
        return self.is_empty() or self.is_full_dimensional()


class ConvexSet_open(ConvexSet_relatively_open):
    r"""
    Abstract base class for open convex sets.
    """

    def is_open(self):
        r"""
        Return whether ``self`` is open.

        OUTPUT:

        Boolean.

        EXAMPLES::

            sage: from sage.geometry.convex_set import ConvexSet_open
            sage: b = ConvexSet_open()
            sage: b.is_open()
            True
        """
        return True

    def is_closed(self):
        r"""
        Return whether ``self`` is closed.

        OUTPUT:

        Boolean.

        EXAMPLES::

            sage: from sage.geometry.convex_set import ConvexSet_open
            sage: class OpenBall(ConvexSet_open):
            ....:     def dim(self):
            ....:         return 3
            ....:     def is_universe(self):
            ....:         return False
            sage: OpenBall().is_closed()
            False
        """
        return self.is_empty() or self.is_universe()
