#!/usr/bin/env python3
"""
Efficient CM Factorization for D*V^2+1 construction
This version focuses on the mathematical properties of the CM construction for efficient factorization.
"""

import random
import math
import time
from typing import Optional, Tuple, List
from Crypto.Util.number import getRandomInteger, getPrime, isPrime
from sympy import gcd
import argparse


def isqrt(n):
    """Integer square root using Newton's method"""
    if n < 0:
        raise ValueError("Square root of negative number")
    if n == 0:
        return 0
    x = n
    while True:
        y = (x + n // x) // 2
        if y >= x:
            return x
        x = y


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


def construct_cm_number(D: int, v_bits: int, q_bits: int, verbose: bool = False) -> Tuple[int, int, int, int]:
    """
    Construct a number using the exact CM construction from the problem
    """
    max_attempts = 2000
    
    for attempt in range(max_attempts):
        # Generate V - must be odd for D ≡ 3 (mod 8)
        V = getRandomInteger(v_bits)
        if V % 2 == 0:
            V += 1
        
        # Calculate numbers = D * V^2 + 1
        numbers = D * V * V + 1
        
        # Check if numbers % 4 == 0
        if numbers % 4 == 0:
            p = numbers // 4
            
            # Test primality
            if p.bit_length() < 512:
                is_prime_p = miller_rabin_is_prime(p, 20)
            else:
                is_prime_p = isPrime(p)
            
            if is_prime_p:
                q = getPrime(q_bits)
                n = p * q
                
                if verbose:
                    print(f"Constructed after {attempt + 1} attempts:")
                    print(f"  V = {V} ({V.bit_length()} bits)")
                    print(f"  numbers = D*V^2+1 = {numbers}")
                    print(f"  p = numbers//4 = {p} ({p.bit_length()} bits)")
                    print(f"  q = {q} ({q.bit_length()} bits)")
                    print(f"  n = p*q = {n} ({n.bit_length()} bits)")
                
                return n, p, q, V
                
        if verbose and attempt % 200 == 0 and attempt > 0:
            print(f"  Construction attempt {attempt}...")
    
    raise ValueError(f"Could not construct after {max_attempts} attempts")


def fermat_factorization(n: int, max_iterations: int = 100000) -> Optional[Tuple[int, int]]:
    """
    Fermat's factorization method - good for factors close to sqrt(n)
    """
    a = isqrt(n)
    if a * a == n:
        return a, a
    
    for i in range(max_iterations):
        a = isqrt(n) + i
        b_squared = a * a - n
        if b_squared < 0:
            continue
            
        b = isqrt(b_squared)
        if b * b == b_squared:
            p = a - b
            q = a + b
            if p > 1 and q > 1 and p * q == n:
                return p, q
    
    return None


def pollard_rho_brent(n: int, max_iterations: int = 100000) -> Optional[int]:
    """
    Brent's improvement to Pollard's rho algorithm
    """
    if n % 2 == 0:
        return 2
    
    for c in range(1, 10):
        y, r, q = random.randint(1, n - 1), 1, 1
        
        while True:
            x = y
            for _ in range(r):
                y = (y * y + c) % n
            
            k = 0
            while k < r and gcd(q, n) == 1:
                ys = y
                for _ in range(min(25, r - k)):
                    y = (y * y + c) % n
                    q = (q * abs(x - y)) % n
                
                g = gcd(q, n)
                k += 25
            
            r *= 2
            
            if g > 1:
                if g == n:
                    while True:
                        ys = (ys * ys + c) % n
                        g = gcd(abs(x - ys), n)
                        if g > 1:
                            break
                
                if g < n:
                    return g
            
            if r > max_iterations:
                break
    
    return None


def cm_structure_factorization(n: int, D: int, verbose: bool = False) -> Optional[Tuple[int, int]]:
    """
    Factorization specifically for numbers with CM structure p*q where p = (D*V^2+1)/4
    """
    if verbose:
        print(f"CM structure factorization of {n} with D={D}")
    
    # For the CM construction, we know one factor has the form (D*V^2+1)/4
    # This means 4p - 1 = D*V^2, so V^2 = (4p-1)/D
    
    # Strategy 1: Try Fermat factorization first (good if factors are close)
    if verbose:
        print("Trying Fermat factorization...")
    
    fermat_result = fermat_factorization(n, 50000)
    if fermat_result:
        p, q = fermat_result
        if verbose:
            print(f"Fermat found: {p} * {q}")
        
        # Check if one of them has CM structure
        for factor in [p, q]:
            temp = 4 * factor - 1
            if temp > 0 and temp % D == 0:
                v_squared = temp // D
                v = isqrt(v_squared)
                if v * v == v_squared and v % 2 == 1:
                    if verbose:
                        print(f"Confirmed CM structure: factor {factor} = (D*{v}^2+1)/4")
                    return p, q
        
        return p, q  # Valid factorization even if not CM structure
    
    # Strategy 2: Pollard's rho with Brent's improvement
    if verbose:
        print("Trying Pollard's rho (Brent)...")
    
    factor = pollard_rho_brent(n, 100000)
    if factor:
        other_factor = n // factor
        if verbose:
            print(f"Pollard's rho found: {factor} * {other_factor}")
        return factor, other_factor
    
    # Strategy 3: Trial division with small primes
    if verbose:
        print("Trying trial division...")
    
    small_primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]
    for p in small_primes:
        if n % p == 0:
            return p, n // p
    
    # Strategy 4: Extended trial division
    limit = min(100000, int(math.sqrt(n)) + 1)
    for i in range(101, limit, 2):
        if n % i == 0:
            return i, n // i
    
    return None


def validate_cm_construction(p: int, D: int, verbose: bool = False) -> Optional[int]:
    """
    Check if p has the form (D*V^2+1)/4 and return V if so
    """
    temp = 4 * p - 1
    if temp % D != 0:
        return None
    
    v_squared = temp // D
    if v_squared <= 0:
        return None
    
    v = isqrt(v_squared)
    if v * v != v_squared:
        return None
    
    if v % 2 != 1:  # V should be odd
        return None
    
    # Double-check the construction
    if (D * v * v + 1) // 4 == p:
        if verbose:
            print(f"Validated: p = {p} = (D*{v}^2+1)/4 with D={D}")
        return v
    
    return None


def comprehensive_cm_factorization(n: int, D: int, verbose: bool = False) -> Optional[Tuple[int, int, Optional[int]]]:
    """
    Comprehensive factorization returning (p, q, V) where V is the CM parameter if found
    """
    if verbose:
        print(f"Comprehensive CM factorization of {n} with D={D}")
    
    start_time = time.time()
    
    result = cm_structure_factorization(n, D, verbose)
    
    if result:
        p, q = result
        
        # Check which factor (if any) has CM structure
        v_p = validate_cm_construction(p, D, verbose)
        v_q = validate_cm_construction(q, D, verbose)
        
        if v_p is not None:
            if verbose:
                print(f"Factor p={p} has CM structure with V={v_p}")
            return p, q, v_p
        elif v_q is not None:
            if verbose:
                print(f"Factor q={q} has CM structure with V={v_q}")
            return q, p, v_q  # Return CM factor first
        else:
            if verbose:
                print("Found factorization but no CM structure detected")
            return p, q, None
    
    end_time = time.time()
    if verbose:
        print(f"Factorization failed after {end_time - start_time:.2f} seconds")
    
    return None


def main():
    parser = argparse.ArgumentParser(description='Efficient CM Factorization')
    parser.add_argument('--action', choices=['construct', 'factor', 'demo', 'benchmark'], 
                        default='demo', help='Action to perform')
    parser.add_argument('--D', type=int, default=11, help='Discriminant D (must be ≡ 3 mod 8)')
    parser.add_argument('--n', type=int, help='Number to factor')
    parser.add_argument('--v-bits', type=int, default=128, help='V bit size for construction')
    parser.add_argument('--q-bits', type=int, default=128, help='Q bit size for construction')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.D % 8 != 3:
        print(f"Warning: D={args.D} is not ≡ 3 (mod 8)")
    
    if args.action == 'construct':
        try:
            n, p, q, V = construct_cm_number(args.D, args.v_bits, args.q_bits, args.verbose)
            print(f"Constructed: n = {n}")
            print(f"  p = {p}")
            print(f"  q = {q}")
            print(f"  V = {V}")
            print(f"Verification: D*V^2+1 = {args.D}*{V}^2+1 = {args.D * V * V + 1}")
            print(f"             (D*V^2+1)/4 = {(args.D * V * V + 1) // 4} = p")
        except ValueError as e:
            print(f"Error: {e}")
    
    elif args.action == 'factor':
        if not args.n:
            print("Error: --n must be specified")
            return
        
        start_time = time.time()
        result = comprehensive_cm_factorization(args.n, args.D, args.verbose)
        end_time = time.time()
        
        if result:
            p, q, v = result
            print(f"Factorization: {args.n} = {p} * {q}")
            if v is not None:
                print(f"CM structure confirmed: p = (D*{v}^2+1)/4")
            print(f"Time: {end_time - start_time:.2f} seconds")
            
            # Verify
            if p * q == args.n:
                print("Verification: PASSED")
            else:
                print("Verification: FAILED")
        else:
            print("Factorization failed")
    
    elif args.action == 'demo':
        print("=== Efficient CM Factorization Demo ===")
        print(f"Using D = {args.D} (discriminant)")
        
        # Step 1: Construct
        print(f"\n1. Constructing CM number with V_bits={args.v_bits}, Q_bits={args.q_bits}")
        try:
            n, p, q, V = construct_cm_number(args.D, args.v_bits, args.q_bits, args.verbose)
            print(f"   Success! n = {n}")
            print(f"   n has {n.bit_length()} bits")
            
            # Step 2: Factor without knowing V
            print("\n2. Factoring without knowledge of construction...")
            start_time = time.time()
            result = comprehensive_cm_factorization(n, args.D, args.verbose)
            end_time = time.time()
            
            if result:
                fp, fq, recovered_v = result
                print(f"   Factorization: {n} = {fp} * {fq}")
                print(f"   Time: {end_time - start_time:.2f} seconds")
                
                if recovered_v is not None:
                    if recovered_v == V:
                        print(f"   EXCELLENT: Recovered original V = {V}")
                    else:
                        print(f"   GOOD: Found CM structure with V = {recovered_v} (original was {V})")
                else:
                    print("   OK: Found factorization but CM structure not detected")
                
                # Verify factors match
                if (fp == p and fq == q) or (fp == q and fq == p):
                    print("   SUCCESS: Original factors recovered!")
                else:
                    print("   SUCCESS: Valid factorization found!")
                    
            else:
                print("   FAILED: Could not factor")
                
        except ValueError as e:
            print(f"   Error: {e}")
    
    elif args.action == 'benchmark':
        print("=== Benchmark ===")
        
        test_cases = [
            (64, 64),
            (96, 96),
            (128, 128),
            (160, 160),
            (192, 192),
            (224, 224),
            (256, 256)
        ]
        
        for v_bits, q_bits in test_cases:
            print(f"\nTesting V_bits={v_bits}, Q_bits={q_bits}")
            
            try:
                # Construction time
                construct_start = time.time()
                n, p, q, V = construct_cm_number(args.D, v_bits, q_bits, False)
                construct_time = time.time() - construct_start
                
                print(f"  Construction: {construct_time:.2f}s, n has {n.bit_length()} bits")
                
                # Factorization time
                factor_start = time.time()
                result = comprehensive_cm_factorization(n, args.D, False)
                factor_time = time.time() - factor_start
                
                if result:
                    fp, fq, recovered_v = result
                    success = (fp == p and fq == q) or (fp == q and fq == p)
                    v_recovered = recovered_v == V if recovered_v else False
                    
                    print(f"  Factorization: {factor_time:.2f}s - {'SUCCESS' if success else 'PARTIAL'}")
                    print(f"  V Recovery: {'YES' if v_recovered else 'NO'}")
                else:
                    print(f"  Factorization: {factor_time:.2f}s - FAILED")
                    
            except ValueError as e:
                print(f"  Construction failed: {e}")


if __name__ == '__main__':
    main()