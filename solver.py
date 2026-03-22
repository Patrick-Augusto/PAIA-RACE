#!/usr/bin/python3

import sys
import random
import time


def read_cnf(file_path):
    clauses = []
    num_vars = 0
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('c'):
                continue
            if line.startswith('p'):
                parts = line.split()
                if len(parts) >= 3:
                    num_vars = int(parts[2])
                continue
            lits = set()
            taut = False
            for x in line.split():
                val = int(x)
                if val == 0:
                    continue
                if -val in lits:
                    taut = True
                    break
                lits.add(val)
            if lits and not taut:
                clauses.append(list(lits))
    return num_vars, clauses


def preprocess(num_vars, clauses):
    """Unit propagation + pure literal elimination."""
    fixed = {}
    changed = True
    while changed:
        changed = False
        new_clauses = []
        for clause in clauses:
            unassigned = []
            sat = False
            for lit in clause:
                v = abs(lit)
                if v in fixed:
                    if (lit > 0) == fixed[v]:
                        sat = True
                        break
                else:
                    unassigned.append(lit)
            if sat:
                continue
            if not unassigned:
                return None, None  # contradiction
            if len(unassigned) == 1:
                v = abs(unassigned[0])
                if v not in fixed:
                    fixed[v] = unassigned[0] > 0
                    changed = True
            new_clauses.append(unassigned)
        clauses = new_clauses

        # Pure literal elimination
        if not changed and clauses:
            pos = set()
            neg = set()
            for clause in clauses:
                for lit in clause:
                    if lit > 0:
                        pos.add(lit)
                    else:
                        neg.add(-lit)
            for v in pos - neg:
                if v not in fixed:
                    fixed[v] = True
                    changed = True
            for v in neg - pos:
                if v not in fixed:
                    fixed[v] = False
                    changed = True
            if changed:
                new_clauses = []
                for clause in clauses:
                    new_clause = []
                    sat = False
                    for lit in clause:
                        v = abs(lit)
                        if v in fixed:
                            if (lit > 0) == fixed[v]:
                                sat = True
                                break
                        else:
                            new_clause.append(lit)
                    if not sat:
                        if not new_clause:
                            return None, None
                        new_clauses.append(new_clause)
                clauses = new_clauses
    return fixed, clauses


def verify(assignment, clauses):
    for clause in clauses:
        ok = False
        for lit in clause:
            v = abs(lit)
            if (lit > 0 and assignment[v]) or (lit < 0 and not assignment[v]):
                ok = True
                break
        if not ok:
            return False
    return True


def dpll_solve(num_vars, clauses, time_limit=3.0):
    """Complete DPLL solver with unit propagation. Returns assignment list or None (UNSAT)."""
    start = time.process_time()

    def unit_propagate(assignment, clauses):
        changed = True
        while changed:
            changed = False
            new_clauses = []
            for cl in clauses:
                unsat_count = 0
                sat = False
                last_unassigned = None
                for lit in cl:
                    v = abs(lit)
                    if assignment[v] == 0:  # unassigned
                        last_unassigned = lit
                        unsat_count += 1
                    elif (lit > 0 and assignment[v] == 1) or (lit < 0 and assignment[v] == -1):
                        sat = True
                        break
                    # else: literal is false, skip
                if sat:
                    continue
                if unsat_count == 0:
                    return None  # conflict
                if unsat_count == 1:
                    v = abs(last_unassigned)
                    assignment[v] = 1 if last_unassigned > 0 else -1
                    changed = True
                else:
                    new_clauses.append(cl)
            clauses = new_clauses
        return clauses

    # assignment: 0=unassigned, 1=True, -1=False
    assignment = [0] * (num_vars + 1)
    stack = [(clauses, assignment[:], None, None)]  # (clauses, assignment, var, phase)

    while stack:
        if time.process_time() - start > time_limit:
            return "TIMEOUT"

        clauses, assignment, var, phase = stack.pop()

        if var is not None:
            assignment[var] = phase
            # Simplify: remove sat clauses, shorten others
            new_clauses = []
            conflict = False
            for cl in clauses:
                sat = False
                remaining = []
                for lit in cl:
                    v = abs(lit)
                    if assignment[v] == 0:
                        remaining.append(lit)
                    elif (lit > 0 and assignment[v] == 1) or (lit < 0 and assignment[v] == -1):
                        sat = True
                        break
                if sat:
                    continue
                if not remaining:
                    conflict = True
                    break
                new_clauses.append(remaining)
            if conflict:
                continue
            clauses = new_clauses

        # Unit propagation
        result = unit_propagate(assignment, clauses)
        if result is None:
            continue  # conflict, backtrack
        clauses = result

        if not clauses:
            return assignment  # SAT

        # Choose variable (VSIDS-like: pick most frequent in shortest clause)
        min_len = len(clauses[0])
        best_cl = clauses[0]
        for cl in clauses:
            if len(cl) < min_len:
                min_len = len(cl)
                best_cl = cl
        branch_var = abs(best_cl[0])

        # Count polarity preference
        pos = 0
        neg = 0
        for cl in clauses:
            for lit in cl:
                if abs(lit) == branch_var:
                    if lit > 0:
                        pos += 1
                    else:
                        neg += 1

        # Push both branches (second push = first tried due to stack LIFO)
        if pos >= neg:
            stack.append((clauses, assignment[:], branch_var, -1))  # try False second
            stack.append((clauses, assignment[:], branch_var, 1))   # try True first
        else:
            stack.append((clauses, assignment[:], branch_var, 1))
            stack.append((clauses, assignment[:], branch_var, -1))

    return None  # UNSAT


def solve(num_vars, clauses, max_time=4.5):
    """Novelty+ with clause weighting and adaptive noise."""
    if not clauses:
        return [0] * (num_vars + 1)

    start = time.process_time()
    nc = len(clauses)

    # Local references for speed
    _random = random.random
    _choice = random.choice
    _randint = random.randint
    _time = time.process_time

    # Build occurrence lists (shared across restarts)
    pos_in = [[] for _ in range(num_vars + 1)]
    neg_in = [[] for _ in range(num_vars + 1)]
    for i, cl in enumerate(clauses):
        for lit in cl:
            if lit > 0:
                pos_in[lit].append(i)
            else:
                neg_in[-lit].append(i)

    # Literal polarity score for initialization bias
    pol = [0] * (num_vars + 1)
    for cl in clauses:
        for lit in cl:
            if lit > 0:
                pol[lit] += 1
            else:
                pol[-lit] -= 1

    best_a = None
    best_u = nc + 1
    restart = 0

    # Clause weights (PAWS-style) — kept across restarts to preserve learned info
    w = [1] * nc

    while _time() - start < max_time:
        restart += 1

        # Adaptive restart length: short restarts early, longer later
        if restart <= 4:
            max_flips = 50000
        elif restart <= 10:
            max_flips = 100000
        else:
            max_flips = 200000

        # Initialize assignment with diverse strategies
        a = [0] * (num_vars + 1)
        strat = restart % 5
        if strat == 1:
            # Polarity bias
            for v in range(1, num_vars + 1):
                a[v] = 1 if pol[v] >= 0 else 0
        elif strat == 2 and best_a is not None:
            # Light perturbation of best (5%)
            for v in range(1, num_vars + 1):
                a[v] = best_a[v]
                if _random() < 0.05:
                    a[v] = 1 - a[v]
        elif strat == 3 and best_a is not None:
            # Heavier perturbation of best (15%)
            for v in range(1, num_vars + 1):
                a[v] = best_a[v]
                if _random() < 0.15:
                    a[v] = 1 - a[v]
        elif strat == 4:
            # Weighted greedy: pick value that satisfies more weighted clauses
            for v in range(1, num_vars + 1):
                sp = sum(w[i] for i in pos_in[v])
                sn = sum(w[i] for i in neg_in[v])
                a[v] = 1 if sp >= sn else 0
        else:
            # Random
            for v in range(1, num_vars + 1):
                a[v] = _randint(0, 1)

        # Initialize sat_count, critical variable, and unsat tracking
        sc = [0] * nc
        crit = [0] * nc
        ul = []
        for i, cl in enumerate(clauses):
            c = 0
            lv = 0
            for lit in cl:
                v = abs(lit)
                if (lit > 0 and a[v]) or (lit < 0 and not a[v]):
                    c += 1
                    lv = v
            sc[i] = c
            if c == 0:
                ul.append(i)
            elif c == 1:
                crit[i] = lv

        up = [-1] * nc
        for i, ci in enumerate(ul):
            up[ci] = i

        # Initialize incremental break scores using current weights
        break_w = [0] * (num_vars + 1)
        for i in range(nc):
            if sc[i] == 1:
                break_w[crit[i]] += w[i]

        # Variable age for Novelty selection
        age = [0] * (num_vars + 1)

        # Adaptive walk probability
        wp = 0.03
        p_nov = 0.3
        best_in_restart = len(ul)
        stale = 0

        for flip in range(1, max_flips + 1):
            if not ul:
                return a

            # Time check every 4096 flips
            if flip & 4095 == 0:
                if _time() - start >= max_time:
                    break

            cur_u = len(ul)

            # Track global best
            if cur_u < best_u:
                best_u = cur_u
                best_a = a[:]

            # Track restart-local progress for noise adaptation
            if cur_u < best_in_restart:
                best_in_restart = cur_u
                stale = 0
            else:
                stale += 1

            # Faster noise adaptation
            if stale > 500:
                wp = min(0.5, wp + 0.02)
                stale = 0
            elif stale == 0:
                wp = max(0.01, wp - 0.01)

            # Select random unsatisfied clause
            ci = _choice(ul)
            cl = clauses[ci]

            if _random() < wp:
                # Random walk step
                bv = abs(_choice(cl))
            else:
                # Novelty+: find best and second-best by break score
                b1s, b1v = nc + 1, -1
                b2s, b2v = nc + 1, -1
                ya, yv = -1, -1

                for lit in cl:
                    v = abs(lit)
                    bc = break_w[v]

                    if bc < b1s:
                        b2s, b2v = b1s, b1v
                        b1s, b1v = bc, v
                    elif bc < b2s:
                        b2s, b2v = bc, v

                    if age[v] > ya:
                        ya = age[v]
                        yv = v

                # Zero break = freebie, always take it
                if b1s == 0:
                    bv = b1v
                elif b1v != yv or b2v == -1:
                    bv = b1v
                else:
                    bv = b2v if _random() < p_nov else b1v

            # Flip variable
            age[bv] = flip
            ov = a[bv]
            nv = 1 - ov
            a[bv] = nv

            # Update clauses where flipped literal becomes false
            tf = pos_in[bv] if ov else neg_in[bv]
            for rc in tf:
                sc_old = sc[rc]
                if sc_old == 1:
                    break_w[crit[rc]] -= w[rc]
                    up[rc] = len(ul)
                    ul.append(rc)
                elif sc_old == 2:
                    for lit2 in clauses[rc]:
                        v2 = abs(lit2)
                        if v2 != bv and ((lit2 > 0 and a[v2]) or (lit2 < 0 and not a[v2])):
                            crit[rc] = v2
                            break_w[v2] += w[rc]
                            break
                sc[rc] = sc_old - 1

            # Update clauses where flipped literal becomes true
            tt = neg_in[bv] if ov else pos_in[bv]
            for rc in tt:
                sc_old = sc[rc]
                if sc_old == 0:
                    crit[rc] = bv
                    break_w[bv] += w[rc]
                    p = up[rc]
                    last = ul[-1]
                    ul[p] = last
                    up[last] = p
                    ul.pop()
                    up[rc] = -1
                elif sc_old == 1:
                    break_w[crit[rc]] -= w[rc]
                sc[rc] = sc_old + 1

            # Clause weight update: increase weights of unsat clauses
            if flip & 255 == 0 and ul:
                for uc in ul:
                    w[uc] += 1
                # Smooth weights periodically to prevent explosion
                if flip & 16383 == 0:
                    for i in range(nc):
                        w[i] = (w[i] + 1) >> 1
                    # Recalculate break scores after weight smoothing
                    break_w = [0] * (num_vars + 1)
                    for i in range(nc):
                        if sc[i] == 1:
                            break_w[crit[i]] += w[i]

    return best_a


def main():
    if len(sys.argv) != 2:
        sys.exit(1)

    num_vars, clauses = read_cnf(sys.argv[1])

    if not clauses:
        print("s SATISFIABLE", flush=True)
        print("v " + " ".join(str(v) for v in range(1, num_vars + 1)) + " 0", flush=True)
        return

    orig_clauses = clauses

    # Preprocessing: unit propagation + pure literal elimination
    fixed, simplified = preprocess(num_vars, clauses)

    if fixed is None:
        # Contradiction detected by unit propagation — formula is UNSAT
        print("s UNSATISFIABLE", flush=True)
        return

    if not simplified:
        # All clauses satisfied by preprocessing alone
        a = [0] * (num_vars + 1)
        for v in range(1, num_vars + 1):
            if v in fixed:
                a[v] = 1 if fixed[v] else 0
            else:
                a[v] = 1
        if verify(a, orig_clauses):
            print("s SATISFIABLE", flush=True)
            res = []
            for v in range(1, num_vars + 1):
                res.append(str(v if a[v] else -v))
            print("v " + " ".join(res) + " 0", flush=True)
        return

    # Find max variable ID in simplified clauses
    mx = 0
    for cl in simplified:
        for lit in cl:
            v = abs(lit)
            if v > mx:
                mx = v

    # Try DPLL complete solver for small instances (can prove UNSAT)
    global_start = time.process_time()
    if mx <= 100:
        dpll_result = dpll_solve(mx, simplified, time_limit=1.0)
    else:
        dpll_result = "TIMEOUT"

    if dpll_result is None:
        # DPLL proved UNSAT
        print("s UNSATISFIABLE", flush=True)
        return
    elif dpll_result != "TIMEOUT":
        # DPLL found SAT solution
        fa = [0] * (num_vars + 1)
        for v in range(1, num_vars + 1):
            if v in fixed:
                fa[v] = 1 if fixed[v] else 0
            elif v <= mx:
                fa[v] = 1 if dpll_result[v] == 1 else 0
        if verify(fa, orig_clauses):
            print("s SATISFIABLE", flush=True)
            res = []
            for v in range(1, num_vars + 1):
                res.append(str(v if fa[v] else -v))
            print("v " + " ".join(res) + " 0", flush=True)
            return

    # Fall back to local search (Novelty+) with remaining time
    elapsed = time.process_time() - global_start
    remaining = max(0.5, 4.5 - elapsed)
    sol = solve(mx, simplified, max_time=remaining)

    if sol:
        # Build full assignment merging preprocessing + search
        fa = [0] * (num_vars + 1)
        for v in range(1, num_vars + 1):
            if v in fixed:
                fa[v] = 1 if fixed[v] else 0
            elif v <= mx:
                fa[v] = sol[v]

        # CRITICAL: verify before output to avoid 10000s bug penalty
        if verify(fa, orig_clauses):
            print("s SATISFIABLE", flush=True)
            res = []
            for v in range(1, num_vars + 1):
                res.append(str(v if fa[v] else -v))
            print("v " + " ".join(res) + " 0", flush=True)
    # If no valid solution found, output nothing — timeout (10s) is far better than bug (50000s)


if __name__ == "__main__":
    main()


