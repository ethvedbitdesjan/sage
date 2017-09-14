r"""
Helper functions for local components

This module contains various functions relating to lifting elements of
`\mathrm{SL}_2(\ZZ / N\ZZ)` to `\mathrm{SL}_2(\ZZ)`, and other related
problems.
"""

from sage.rings.all import ZZ
from sage.arith.all import crt, inverse_mod
from sage.modular.modsym.p1list import lift_to_sl2z
from copy import copy


def lift_to_gamma1(g, m, n):
    r"""
    If ``g = [a,b,c,d]`` is a list of integers defining a `2 \times 2` matrix
    whose determinant is `1 \pmod m`, return a list of integers giving the
    entries of a matrix which is congruent to `g \pmod m` and to
    `\begin{pmatrix} 1 & * \\ 0 & 1 \end{pmatrix} \pmod n`. Here `m` and `n`
    must be coprime.

    Here `m` and `n` should be coprime positive integers. Either of `m` and `n`
    can be `1`. If `n = 1`, this still makes perfect sense; this is what is
    called by the function :func:`~lift_matrix_to_sl2z`. If `m = 1` this is a
    rather silly question, so we adopt the convention of always returning the
    identity matrix.

    The result is always a list of Sage integers (unlike ``lift_to_sl2z``,
    which tends to return Python ints).

    EXAMPLES::

        sage: from sage.modular.local_comp.liftings import lift_to_gamma1
        sage: A = matrix(ZZ, 2, lift_to_gamma1([10, 11, 3, 11], 19, 5)); A
        [371  68]
        [ 60  11]
        sage: A.det() == 1
        True
        sage: A.change_ring(Zmod(19))
        [10 11]
        [ 3 11]
        sage: A.change_ring(Zmod(5))
        [1 3]
        [0 1]
        sage: m = list(SL2Z.random_element())
        sage: n = lift_to_gamma1(m, 11, 17)
        sage: assert matrix(Zmod(11), 2, n) == matrix(Zmod(11),2,m)
        sage: assert matrix(Zmod(17), 2, [n[0], 0, n[2], n[3]]) == 1
        sage: type(lift_to_gamma1([10,11,3,11],19,5)[0])
        <type 'sage.rings.integer.Integer'>

    Tests with `m = 1` and with `n = 1`::

        sage: lift_to_gamma1([1,1,0,1], 5, 1)
        [1, 1, 0, 1]
        sage: lift_to_gamma1([2,3,11,22], 1, 5)
        [1, 0, 0, 1]
    """
    if m == 1:
        return [ZZ.one(), ZZ.zero(), ZZ.zero(), ZZ.one()]
    a, b, c, d = [ZZ(x) for x in g]
    det = (a * d - b * c) % m
    if det != 1:
        raise ValueError("Determinant is {0} mod {1}, should be 1".format(det, m))
    c2 = crt(c, 0, m, n)
    d2 = crt(d, 1, m, n)
    a3,b3,c3,d3 = [ZZ(_) for _ in lift_to_sl2z(c2, d2, m * n)]
    r = (a3*b - b3*a) % m
    return [a3 + r * c3, b3 + r * d3, c3, d3]


def lift_matrix_to_sl2z(A, N):
    r"""
    Given a list of length 4 representing a 2x2 matrix over `\ZZ / N\ZZ` with
    determinant 1 (mod `N`), lift it to a 2x2 matrix over `\ZZ` with
    determinant 1.

    This is a special case of :func:`~lift_to_gamma1`, and is coded as such.

    EXAMPLES::

        sage: from sage.modular.local_comp.liftings import lift_matrix_to_sl2z
        sage: lift_matrix_to_sl2z([10, 11, 3, 11], 19)
        [29, 106, 3, 11]
        sage: type(_[0])
        <type 'sage.rings.integer.Integer'>
        sage: lift_matrix_to_sl2z([2,0,0,1], 5)
        Traceback (most recent call last):
        ...
        ValueError: Determinant is 2 mod 5, should be 1
    """
    return lift_to_gamma1(A, N, 1)


def lift_gen_to_gamma1(m, n):
    r"""
    Return four integers defining a matrix in `\mathrm{SL}_2(\ZZ)` which is
    congruent to `\begin{pmatrix} 0 & -1 \\ 1 & 0 \end{pmatrix} \pmod m` and
    lies in the subgroup `\begin{pmatrix} 1 & * \\ 0 & 1 \end{pmatrix} \pmod
    n`.

    This is a special case of :func:`~lift_to_gamma1`, and is coded as such.

    EXAMPLES::

        sage: from sage.modular.local_comp.liftings import lift_gen_to_gamma1
        sage: A = matrix(ZZ, 2, lift_gen_to_gamma1(9, 8)); A
        [441  62]
        [ 64   9]
        sage: A.change_ring(Zmod(9))
        [0 8]
        [1 0]
        sage: A.change_ring(Zmod(8))
        [1 6]
        [0 1]
        sage: type(lift_gen_to_gamma1(9, 8)[0])
        <type 'sage.rings.integer.Integer'>
    """
    return lift_to_gamma1([0,-1,1,0], m, n)


def lift_uniformiser_odd(p, u, n):
    r"""
    Construct a matrix over `\ZZ` whose determinant is `p`, and which is
    congruent to `\begin{pmatrix} 0 & -1 \\ p & 0 \end{pmatrix} \pmod{p^u}` and
    to `\begin{pmatrix} p & 0 \\ 0 & 1\end{pmatrix} \pmod n`.

    This is required for the local components machinery in the "ramified" case
    (when the exponent of `p` dividing the level is odd).

    EXAMPLES::

        sage: from sage.modular.local_comp.liftings import lift_uniformiser_odd
        sage: lift_uniformiser_odd(3, 2, 11)
        [432, 377, 165, 144]
        sage: type(lift_uniformiser_odd(3, 2, 11)[0])
        <type 'sage.rings.integer.Integer'>
    """
    g = lift_gen_to_gamma1(p**u, n)
    return [p * g[0], g[1], p * g[2], g[3]]


def lift_ramified(g, p, u, n):
    r"""
    Given four integers `a,b,c,d` with `p \mid c` and `ad - bc = 1 \pmod{p^u}`,
    find `a',b',c',d'` congruent to `a,b,c,d \pmod{p^u}`, with `c' = c
    \pmod{p^{u+1}}`, such that `a'd' - b'c'` is exactly 1, and `\begin{pmatrix}
    a & b \\ c & d \end{pmatrix}` is in `\Gamma_1(n)`.

    Algorithm: Uses :func:`~lift_to_gamma1` to get a lifting modulo `p^u`, and
    then adds an appropriate multiple of the top row to the bottom row in order
    to get the bottom-left entry correct modulo `p^{u+1}`.

    EXAMPLES::

        sage: from sage.modular.local_comp.liftings import lift_ramified
        sage: lift_ramified([2,2,3,2], 3, 1, 1)
        [5, 8, 3, 5]
        sage: lift_ramified([8,2,12,2], 3, 2, 23)
        [323, 110, -133584, -45493]
        sage: type(lift_ramified([8,2,12,2], 3, 2, 23)[0])
        <type 'sage.rings.integer.Integer'>
    """
    a,b,c,d = lift_to_gamma1(g, p**u, n)
    r = crt( (c - g[2]) / p**u * inverse_mod(a, p), 0, p, n)
    c = c - p**u * r * a
    d = d - p**u * r * b
    # assert (c - g[2]) % p**(u+1) == 0
    return [a,b,c,d]


def lift_for_SL(A, N):
    r"""
    Lift a matrix `A` from `SL_m(\ZZ / N\ZZ)` to `SL_m(\ZZ)`.

    Follows Shimura, Lemma 1.38, p. 21.

    EXAMPLES::


        sage: from sage.modular.local_comp.liftings import lift_for_SL
        sage: N = 11
        sage: A = matrix(ZZ, 4, 4, [6, 0, 0, 9, 1, 6, 9, 4, 4, 4, 8, 0, 4, 0, 0, 8])
        sage: A.det()
        144
        sage: A.change_ring(Zmod(N)).det()
        1
        sage: L = lift_for_SL(A, N)
        sage: L.det()
        1
        sage: (L - A) * Mod(1, N) == 0
        True

        sage: N = 19
        sage: B = matrix(ZZ, 4, 4, [1, 6, 10, 4, 4, 14, 15, 4, 13, 0, 1, 15, 15, 15, 17, 10])
        sage: B.det()
        4447
        sage: B.change_ring(Zmod(N)).det()
        1
        sage: L = lift_for_SL(B, N)
        sage: L.det()
        1
        sage: (L - B) * Mod(1, N) == 0
        True
    """
    from sage.matrix.constructor import matrix
    from sage.matrix.special import identity_matrix, diagonal_matrix, block_diagonal_matrix
    from sage.misc.misc_c import prod

    m = A.nrows()
    if m == 1:
        return identity_matrix(1)

    D, U, V = A.smith_form()
    diag = diagonal_matrix([-1] + [1] * (m - 1))
    if U.det() == -1 :
        U = diag * U
    if V.det() == -1 :
        V = V * diag
    D = U * A * V

    a = [D[i, i] for i in range(m)]
    b = prod(a[1:])
    W = identity_matrix(m)
    W[0, 0] = b
    W[1, 0] = b - 1
    W[0, 1] = 1

    X = identity_matrix(m)
    X[0, 1] = -a[1]

    Ap = copy(D)
    Ap[0, 0] = 1
    Ap[1, 0] = 1 - a[0]
    Ap[1, 1] *= a[0]

    Cp = diagonal_matrix(a[1:])
    Cp[0, 0] *= a[0]
    C = lift_for_SL(Cp, N)

    Cpp = block_diagonal_matrix(identity_matrix(1), C)
    Cpp[1, 0] = 1 - a[0]

    return (~U * ~W * Cpp * ~X * ~V).change_ring(ZZ)
