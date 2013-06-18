import operator
import cPickle
import random
import math
from itertools import *

primes = cPickle.Unpickler(open("10000_primes.pkl")).load()
log_max_primorial = 150606

def _successors(n, s):
    return [ (2*i + 1) % n for i in s ]

def _allowed_residues(n):
    """For a given number n, find the allowed residues mod n that will not obviously invalidate primality"""
    possibilities = range(n)
    first_residues = _successors(n, possibilities)
    second_residues = _successors(n, first_residues)
    return [ r for (i, r) in enumerate(possibilities)
             if r != 0
             if first_residues[i] != 0
             if second_residues[i] != 0 ]

def _choice(s):
    # random.choice is implemented wrong, so we do it ourselves
    if len(s) == 1:
        return s[0]
    l = int(math.ceil(math.log(len(s),2)))
    i = len(s)
    while i >= len(s):
        i = random.getrandbits(l)
    return s[i]

def generate_naive(i):
    """
    Generate the exhaustive list of all residues mod the i'th primorial that do not obviously violate primality
    returns a tuple (i'th primorial, list of residues)
    """
    pairs = [ (n,set(_allowed_residues(n))) for n in primes[:i]]
    m = reduce(operator.mul, map(operator.itemgetter(0), pairs))
    residues = [ r for r in xrange(m)
                 if all(map(lambda (n,rs): (r % n) in rs, pairs)) ]
    return (m,residues)

class Sieve(object):
    """An efficient way of representing the allowed residues for the i'th primorial"""
    def __init__(self, mod_bits):
        """Argument mod_bits is the maximum length of the modulus"""
        if mod_bits >= log_max_primorial:
            raise ValueError("Requested modulus is too large")
        max_index = len(primes)+1
        min_index = 1
        index = None
        while max_index > min_index:
            index = (max_index + min_index) / 2
            m = reduce(operator.mul, primes[:index])
            if m >> mod_bits:
                # too big
                max_index = index
            elif not (m >> (mod_bits - 1)):
                # too small
                if index == min_index:
                    # we do floor division for the average, so we can get stuck here
                    break
                min_index = index
            else:
                break

        assert (1 << mod_bits) > m
        assert (1 << mod_bits) < reduce(operator.mul, primes[:index+1])
        self.index = index = int(round(index))
        self.modulus = m
        self.residues = [ (n, _allowed_residues(n), ((m*pow(m/n,n-2,n))/n) % m) for n in primes[:index] ]
        num_residues = reduce(operator.mul, map(len, map(operator.itemgetter(1), self.residues)))
        try:
            self.advantage = float(num_residues) / self.modulus
        except OverflowError:
            self.advantage = math.exp(math.log(num_residues) - math.log(self.modulus))

    def make_candidate(self, bits, random=random):
        """Argument bits is the maximum length of the candidate generated"""
        # avoid doing multiple dictionary lookups
        modulus = self.modulus
        choice = _choice
        
        rand_bits = bits
        rand_bits -= math.floor(math.log(self.modulus,2)) # we get these bits by multiplying by the modulus and adding the residue
        rand_bits -= 1 # we always set the high bit
        rand_bits = int(math.ceil(rand_bits))
        bits = int(math.ceil(bits))

        residue = 0
        for (n,s,e) in self.residues:
            residue = (residue + e*choice(s)) % modulus
        assert modulus > residue

        candidate = random.getrandbits(rand_bits)
        candidate |= (1 << (rand_bits))
        candidate *= self.modulus
        candidate += residue
        if candidate >> bits:
            return self.make_candidate(bits, random)
        else:
            return candidate

    def _check(self):
        """Check this sieve against the naive implementation. For i>8, takes huge amounts of time."""
        residues = list()
        for j in product(*map(operator.itemgetter(1), self.residues)):
            residue = 0
            for (k, e) in izip(j, imap(operator.itemgetter(2), self.residues)):
                residue += k*e
            residues.append(residue % self.modulus)
        residues.sort()

        (m, other_residues) = generate_naive(len(self.residues))
        assert (m == self.modulus and residues == other_residues)


__all__ = ["Sieve", "generate_naive"]
