#!/usr/bin/env python3
"""
Optimized CM Factorization for D*V^2+1 construction
This is an improved version that uses more advanced techniques for factorization.
"""

import random
import math
import time
from typing import Optional, Tuple, List
from Crypto.Util.number import getRandomInteger, getPrime, isPrime
from sympy import factorint, gcd
import argparse


def isqrt(n):
    """Integer square root"""
    if n < 0:
        raise ValueError("Square root of negative number")
    if n == 0:
        return 0
    x = n
    y = (x + 1) // 2
    while y < x:
        x = y
        y = (x + n // x) // 2
    return x


def miller_rabin_is_prime(n: int, k: int = 10) -> bool:
    """Miller-Rabin primality test"""
    if n < 2:
        return False
    if n == 2 or n == 3:
        return True
    if n % 2 == 0:
        return False
    
    r = 0
    d = n - 1
    while d % 2 == 0:
        r += 1
        d //= 2
    
    for _ in range(k):
        a = random.randrange(2, n - 1)
        x = pow(a, d, n)
        
        if x == 1 or x == n - 1:
            continue
            
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    
    return True


def pollard_rho(n: int, max_iterations: int = 100000) -> Optional[int]:
    """Pollard's rho algorithm with cycle detection"""
    if n % 2 == 0:
        return 2
    
    for c in range(1, 10):  # Try different c values
        x = random.randint(2, n - 2)
        y = x
        d = 1
        
        for _ in range(max_iterations):
            x = (x * x + c) % n
            y = (y * y + c) % n
            y = (y * y + c) % n
            
            d = gcd(abs(x - y), n)
            
            if d != 1 and d != n:
                return d
    
    return None


def trial_division(n: int, limit: int = 1000000) -> Optional[int]:
    """Trial division up to limit"""
    if n % 2 == 0:
        return 2
    
    for i in range(3, min(limit, int(math.sqrt(n)) + 1), 2):
        if n % i == 0:
            return i
    
    return None


def construct_with_known_structure(D: int, v_bits: int, q_bits: int, verbose: bool = False) -> Tuple[int, int, int, int]:
    """Construct a number using the exact structure from the problem statement"""
    max_attempts = 1000
    
    for attempt in range(max_attempts):
        # Generate V as specified
        V = getRandomInteger(v_bits)
        if V % 2 == 0:
            V += 1  # Ensure V is odd for D ≡ 3 (mod 8)
        
        # Calculate numbers = D * V^2 + 1
        numbers = D * V * V + 1
        
        # Check the condition from the problem statement
        if numbers % 4 == 0:
            p = numbers // 4
            
            # Check if p is prime
            if p.bit_length() < 512:
                is_prime_p = miller_rabin_is_prime(p, 20)
            else:
                is_prime_p = isPrime(p)
            
            if is_prime_p:
                # Generate q as specified
                q = getPrime(q_bits)
                n = p * q
                
                if verbose:
                    print(f"Successfully constructed after {attempt + 1} attempts:")
                    print(f"  V = {V} ({V.bit_length()} bits)")
                    print(f"  p = (D*V^2+1)/4 = {p} ({p.bit_length()} bits)")
                    print(f"  q = {q} ({q.bit_length()} bits)")
                    print(f"  n = p*q = {n} ({n.bit_length()} bits)")
                
                return n, p, q, V
                
        if verbose and attempt % 100 == 0 and attempt > 0:
            print(f"  Attempt {attempt}...")
    
    raise ValueError(f"Could not construct number after {max_attempts} attempts")


def smart_cm_factorization(n: int, D: int, verbose: bool = False) -> Optional[Tuple[int, int]]:
    """
    Smart factorization for numbers of the form p*q where p = (D*V^2+1)/4
    """
    if verbose:
        print(f"Attempting smart CM factorization of {n} with D={D}")
    
    # Strategy 1: Try small factors first
    small_factor = trial_division(n, 10000)
    if small_factor:
        return small_factor, n // small_factor
    
    # Strategy 2: Try Pollard's rho
    if verbose:
        print("Trying Pollard's rho...")
    
    rho_factor = pollard_rho(n, 100000)
    if rho_factor:
        if verbose:
            print(f"Pollard's rho found factor: {rho_factor}")
        return rho_factor, n // rho_factor
    
    # Strategy 3: Use the fact that one factor has the form (D*V^2+1)/4
    # We can search for V values that might work
    if verbose:
        print("Searching for V values...")
    
    # Estimate the bit size of V from n
    n_bits = n.bit_length()
    estimated_v_bits = n_bits // 4  # Very rough estimate
    
    # Try different V bit sizes around the estimate
    for v_bits in range(max(64, estimated_v_bits - 64), estimated_v_bits + 64, 16):
        if verbose:
            print(f"  Trying V with {v_bits} bits...")
        
        # For each bit size, try a limited number of V values
        v_min = 1 << (v_bits - 1)
        v_max = (1 << v_bits) - 1
        
        for _ in range(1000):  # Try 1000 random V values
            V = random.randrange(v_min, v_max)
            if V % 2 == 0:
                V += 1  # Make odd
            
            # Calculate the corresponding p
            numbers = D * V * V + 1
            if numbers % 4 == 0:
                p = numbers // 4
                
                # Check if p divides n
                if n % p == 0:
                    q = n // p
                    if verbose:
                        print(f"Found factorization: {n} = {p} * {q}")
                        print(f"Where p = (D*{V}^2+1)/4")
                    return p, q
    
    return None


def enhanced_cm_search(n: int, D: int, verbose: bool = False) -> Optional[Tuple[int, int]]:
    """
    Enhanced search using mathematical properties of CM construction
    """
    if verbose:
        print("Enhanced CM search...")
    
    # Since p = (D*V^2 + 1)/4, we have 4p = D*V^2 + 1
    # So V^2 = (4p - 1)/D
    # If we can guess p (factor of n), we can check if (4p-1)/D is a perfect square
    
    # Try some potential factors of n using various methods
    potential_factors = []
    
    # Add some factors found by trial division
    for i in range(3, min(100000, int(math.sqrt(n)) + 1), 2):
        if n % i == 0:
            potential_factors.append(i)
            potential_factors.append(n // i)
    
    # Add factors from Pollard's rho with different parameters
    for c in range(1, 20):
        x = random.randint(2, n - 2)
        y = x
        d = 1
        
        for _ in range(10000):
            x = (x * x + c) % n
            y = (y * y + c) % n
            y = (y * y + c) % n
            
            d = gcd(abs(x - y), n)
            
            if d != 1 and d != n:
                potential_factors.append(d)
                potential_factors.append(n // d)
                break
    
    # Check each potential factor
    for p in potential_factors:
        if p == 1 or p == n:
            continue
            
        # Check if this could be a CM prime: p = (D*V^2 + 1)/4
        temp = 4 * p - 1
        if temp % D == 0:
            v_squared = temp // D
            if v_squared > 0:
                v = isqrt(v_squared)
                if v * v == v_squared and v % 2 == 1:  # Perfect square and odd V
                    if verbose:
                        print(f"Found CM factorization: p={p}, V={v}")
                    return p, n // p
    
    return None


def comprehensive_factorization(n: int, D: int, verbose: bool = False) -> Optional[Tuple[int, int]]:
    """
    Comprehensive factorization combining multiple techniques
    """
    if verbose:
        print(f"Comprehensive factorization of {n} (D={D})")
    
    start_time = time.time()
    
    # Method 1: Smart CM factorization
    result = smart_cm_factorization(n, D, verbose)
    if result:
        return result
    
    # Method 2: Enhanced CM search
    result = enhanced_cm_search(n, D, verbose)
    if result:
        return result
    
    # Method 3: Extended Pollard's rho with multiple attempts
    if verbose:
        print("Extended Pollard's rho attempts...")
    
    for _ in range(50):  # Multiple attempts with different random starts
        factor = pollard_rho(n, 200000)
        if factor:
            if verbose:
                print(f"Extended Pollard's rho found: {factor}")
            return factor, n // factor
    
    end_time = time.time()
    if verbose:
        print(f"Factorization failed after {end_time - start_time:.2f} seconds")
    
    return None


def main():
    parser = argparse.ArgumentParser(description='Optimized CM Factorization')
    parser.add_argument('--action', choices=['construct', 'factor', 'demo', 'benchmark'], 
                        default='demo', help='Action to perform')
    parser.add_argument('--D', type=int, default=11, help='Discriminant D')
    parser.add_argument('--n', type=int, help='Number to factor')
    parser.add_argument('--v-bits', type=int, default=256, help='V bit size')
    parser.add_argument('--q-bits', type=int, default=256, help='Q bit size')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.action == 'construct':
        try:
            n, p, q, V = construct_with_known_structure(args.D, args.v_bits, args.q_bits, args.verbose)
            print(f"Constructed number: {n}")
            print(f"Factors: {p} * {q}")
            print(f"V value: {V}")
        except ValueError as e:
            print(f"Error: {e}")
    
    elif args.action == 'factor':
        if not args.n:
            print("Error: --n must be specified for factor action")
            return
        
        start_time = time.time()
        result = comprehensive_factorization(args.n, args.D, args.verbose)
        end_time = time.time()
        
        if result:
            p, q = result
            print(f"Factorization: {args.n} = {p} * {q}")
            print(f"Time: {end_time - start_time:.2f} seconds")
            
            # Verify
            if p * q == args.n:
                print("Verification: PASSED")
            else:
                print("Verification: FAILED")
        else:
            print("Factorization failed")
    
    elif args.action == 'demo':
        print("=== Optimized CM Factorization Demo ===")
        
        # Construct a number
        print(f"\n1. Constructing number with D={args.D}, V_bits={args.v_bits}, Q_bits={args.q_bits}")
        try:
            n, p, q, V = construct_with_known_structure(args.D, args.v_bits, args.q_bits, args.verbose)
            print(f"   n = {n}")
            
            # Factor it back (without using V)
            print("\n2. Factoring without knowledge of V...")
            start_time = time.time()
            result = comprehensive_factorization(n, args.D, args.verbose)
            end_time = time.time()
            
            if result:
                fp, fq = result
                print(f"   Found: {n} = {fp} * {fq}")
                print(f"   Time: {end_time - start_time:.2f} seconds")
                
                if (fp == p and fq == q) or (fp == q and fq == p):
                    print("   SUCCESS: Original factors recovered!")
                else:
                    print("   SUCCESS: Valid factorization found!")
            else:
                print("   FAILED: Could not factor")
                
        except ValueError as e:
            print(f"Error: {e}")
    
    elif args.action == 'benchmark':
        print("=== Benchmark ===")
        
        bit_sizes = [(128, 128), (256, 256), (384, 384), (512, 512)]
        
        for v_bits, q_bits in bit_sizes:
            print(f"\nTesting with V_bits={v_bits}, Q_bits={q_bits}")
            
            try:
                # Construct
                construct_start = time.time()
                n, p, q, V = construct_with_known_structure(args.D, v_bits, q_bits, False)
                construct_time = time.time() - construct_start
                
                print(f"  Construction: {construct_time:.2f}s, n has {n.bit_length()} bits")
                
                # Factor
                factor_start = time.time()
                result = comprehensive_factorization(n, args.D, False)
                factor_time = time.time() - factor_start
                
                if result:
                    print(f"  Factorization: {factor_time:.2f}s - SUCCESS")
                else:
                    print(f"  Factorization: {factor_time:.2f}s - FAILED")
                    
            except ValueError as e:
                print(f"  Error: {e}")


if __name__ == '__main__':
    main()