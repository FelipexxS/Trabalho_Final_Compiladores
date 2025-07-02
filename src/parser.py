class Parser:
    def __init__(self, rules, nonterm_userdef, term_userdef, sample_input_string=None):
        self.rules = rules
        self.nonterm_userdef = nonterm_userdef
        self.term_userdef = term_userdef
        self.sample_input_string = sample_input_string
        self.diction = {}
        self.firsts = {}
        self.follows = {}
        self.start_symbol = None

    def removeLeftRecursion(self, rulesDiction):
        store = {}
        for lhs in rulesDiction:
            alphaRules = []
            betaRules = []
            allrhs = rulesDiction[lhs]
            for subrhs in allrhs:
                if subrhs[0] == lhs:
                    alphaRules.append(subrhs[1:])
                else:
                    betaRules.append(subrhs)
            if len(alphaRules) != 0:
                lhs_ = lhs + "'"
                while (lhs_ in rulesDiction.keys()) or (lhs_ in store.keys()):
                    lhs_ += "'"
                for b in range(0, len(betaRules)):
                    betaRules[b].append(lhs_)
                rulesDiction[lhs] = betaRules
                for a in range(0, len(alphaRules)):
                    alphaRules[a].append(lhs_)
                alphaRules.append(['#'])
                store[lhs_] = alphaRules
        for left in store:
            rulesDiction[left] = store[left]
        self.diction = rulesDiction

    def LeftFactoring(self, rulesDiction):
        newDict = {}
        for lhs in rulesDiction:
            allrhs = rulesDiction[lhs]
            temp = dict()
            for subrhs in allrhs:
                if subrhs[0] not in list(temp.keys()):
                    temp[subrhs[0]] = [subrhs]
                else:
                    temp[subrhs[0]].append(subrhs)
            new_rule = []
            tempo_dict = {}
            for term_key in temp:
                allStartingWithTermKey = temp[term_key]
                if len(allStartingWithTermKey) > 1:
                    lhs_ = lhs + "'"
                    while (lhs_ in rulesDiction.keys()) or (lhs_ in tempo_dict.keys()):
                        lhs_ += "'"
                    new_rule.append([term_key, lhs_])
                    ex_rules = []
                    for g in temp[term_key]:
                        ex_rules.append(g[1:])
                    tempo_dict[lhs_] = ex_rules
                else:
                    new_rule.append(allStartingWithTermKey[0])
            newDict[lhs] = new_rule
            for key in tempo_dict:
                newDict[key] = tempo_dict[key]
        self.diction = newDict

    def first(self, rule):
        if len(rule) != 0 and (rule is not None):
            if rule[0] in self.term_userdef:
                return rule[0]
            elif rule[0] == '#':
                return '#'
        if len(rule) != 0:
            if rule[0] in list(self.diction.keys()):
                fres = []
                rhs_rules = self.diction[rule[0]]
                for itr in rhs_rules:
                    indivRes = self.first(itr)
                    if type(indivRes) is list:
                        for i in indivRes:
                            fres.append(i)
                    else:
                        fres.append(indivRes)
                if '#' not in fres:
                    return fres
                else:
                    newList = []
                    fres.remove('#')
                    if len(rule) > 1:
                        ansNew = self.first(rule[1:])
                        if ansNew is not None:
                            if type(ansNew) is list:
                                newList = fres + ansNew
                            else:
                                newList = fres + [ansNew]
                        else:
                            newList = fres
                        return newList
                    fres.append('#')
                    return fres

    def follow(self, nt):
        solset = set()
        if nt == self.start_symbol:
            solset.add('$')
        for curNT in self.diction:
            rhs = self.diction[curNT]
            for subrule in rhs:
                if nt in subrule:
                    while nt in subrule:
                        index_nt = subrule.index(nt)
                        subrule = subrule[index_nt + 1:]
                        if len(subrule) != 0:
                            res = self.first(subrule)
                            if '#' in res:
                                newList = []
                                res = list(res)
                                res.remove('#')
                                ansNew = self.follow(curNT)
                                if ansNew is not None:
                                    if type(ansNew) is list:
                                        newList = res + ansNew
                                    else:
                                        newList = res + [ansNew]
                                else:
                                    newList = res
                                res = newList
                        else:
                            if nt != curNT:
                                res = self.follow(curNT)
                        if res is not None:
                            if type(res) is list:
                                for g in res:
                                    solset.add(g)
                            else:
                                solset.add(res)
        return list(solset)

    def computeAllFirsts(self):
        for rule in self.rules:
            k = rule.split("->")
            k[0] = k[0].strip()
            k[1] = k[1].strip()
            rhs = k[1]
            multirhs = rhs.split('|')
            for i in range(len(multirhs)):
                multirhs[i] = multirhs[i].strip()
                multirhs[i] = multirhs[i].split()
            self.diction[k[0]] = multirhs

        print(f"\nRules: \n")
        for y in self.diction:
            print(f"{y}->{self.diction[y]}")
        print(f"\nAfter elimination of left recursion:\n")

        self.removeLeftRecursion(self.diction)
        for y in self.diction:
            print(f"{y}->{self.diction[y]}")
        print("\nAfter left factoring:\n")

        self.LeftFactoring(self.diction)
        for y in self.diction:
            print(f"{y}->{self.diction[y]}")

        for y in list(self.diction.keys()):
            t = set()
            for sub in self.diction.get(y):
                res = self.first(sub)
                if res is not None:
                    if type(res) is list:
                        for u in res:
                            t.add(u)
                    else:
                        t.add(res)
            self.firsts[y] = t

        print("\nCalculated firsts: ")
        key_list = list(self.firsts.keys())
        index = 0
        for gg in self.firsts:
            print(f"first({key_list[index]}) => {self.firsts.get(gg)}")
            index += 1

    def computeAllFollows(self):
        for NT in self.diction:
            solset = set()
            sol = self.follow(NT)
            if sol is not None:
                for g in sol:
                    solset.add(g)
            self.follows[NT] = solset

        print("\nCalculated follows: ")
        key_list = list(self.follows.keys())
        index = 0
        for gg in self.follows:
            print(f"follow({key_list[index]}) => {self.follows[gg]}")
            index += 1

    def createParseTable(self):
        import copy
        print("\nFirsts and Follow Result table\n")
        mx_len_first = 0
        mx_len_fol = 0
        for u in self.diction:
            k1 = len(str(self.firsts[u]))
            k2 = len(str(self.follows[u]))
            if k1 > mx_len_first:
                mx_len_first = k1
            if k2 > mx_len_fol:
                mx_len_fol = k2

        print(f"{{:<{10}}} {{:<{mx_len_first + 5}}} {{:<{mx_len_fol + 5}}}".format("Non-T", "FIRST", "FOLLOW"))
        for u in self.diction:
            print(f"{{:<{10}}} {{:<{mx_len_first + 5}}} {{:<{mx_len_fol + 5}}}".format(u, str(self.firsts[u]), str(self.follows[u])))

        ntlist = list(self.diction.keys())
        terminals = copy.deepcopy(self.term_userdef)
        terminals.append('$')

        mat = []
        for x in self.diction:
            row = []
            for y in terminals:
                row.append('')
            mat.append(row)

        grammar_is_LL = True

        for lhs in self.diction:
            rhs = self.diction[lhs]
            for y in rhs:
                res = self.first(y)
                if '#' in res:
                    if type(res) == str:
                        firstFollow = []
                        fol_op = self.follows[lhs]
                        if isinstance(fol_op, str):
                            firstFollow.append(fol_op)
                        else:
                            for u in fol_op:
                                firstFollow.append(u)
                        res = firstFollow
                    else:
                        res = list(res)
                        res.remove('#')
                        res = list(res) + list(self.follows[lhs])
                ttemp = []
                if type(res) is str:
                    ttemp.append(res)
                    res = copy.deepcopy(ttemp)
                for c in res:
                    xnt = ntlist.index(lhs)
                    yt = terminals.index(c)
                    if mat[xnt][yt] == '':
                        mat[xnt][yt] = mat[xnt][yt] + f"{lhs}->{' '.join(y)}"
                    else:
                        if f"{lhs}->{y}" in mat[xnt][yt]:
                            continue
                        else:
                            grammar_is_LL = False
                            mat[xnt][yt] = mat[xnt][yt] + f",{lhs}->{' '.join(y)}"

        print("\nGenerated parsing table:\n")
        frmt = "{:>12}" * len(terminals)
        print(frmt.format(*terminals))

        j = 0
        for y in mat:
            frmt1 = "{:>12}" * len(y)
            print(f"{ntlist[j]} {frmt1.format(*y)}")
            j += 1

        return (mat, grammar_is_LL, terminals)

    def validateStringUsingStackBuffer(self, parsing_table, grammarll1, table_term_list, input_string):
        print(f"\nValidate String => {input_string}\n")
        if grammarll1 == False:
            return f"\nInput String = \"{input_string}\"\nGrammar is not LL(1)"
        stack = [self.start_symbol, '$']
        input_string = input_string.split()
        input_string.reverse()
        buffer = ['$'] + input_string

        print("{:>20} {:>20} {:>20}".format("Buffer", "Stack", "Action"))

        while True:
            if stack == ['$'] and buffer == ['$']:
                print("{:>20} {:>20} {:>20}".format(' '.join(buffer), ' '.join(stack), "Valid"))
                return "\nValid String!"
            elif stack[0] not in self.term_userdef:
                x = list(self.diction.keys()).index(stack[0])
                y = table_term_list.index(buffer[-1])
                if parsing_table[x][y] != '':
                    entry = parsing_table[x][y]
                    print("{:>20} {:>20} {:>25}".format(' '.join(buffer), ' '.join(stack), f"T[{stack[0]}][{buffer[-1]}] = {entry}"))
                    lhs_rhs = entry.split("->")
                    lhs_rhs[1] = lhs_rhs[1].replace('#', '').strip()
                    entryrhs = lhs_rhs[1].split()
                    stack = entryrhs + stack[1:]
                else:
                    return f"\nInvalid String! No rule at Table[{stack[0]}][{buffer[-1]}]."
            else:
                if stack[0] == buffer[-1]:
                    print("{:>20} {:>20} {:>20}".format(' '.join(buffer), ' '.join(stack), f"Matched:{stack[0]}"))
                    buffer = buffer[:-1]
                    stack = stack[1:]
                else:
                    return "\nInvalid String! Unmatched terminal symbols"

    def run(self):
        self.computeAllFirsts()
        self.start_symbol = list(self.diction.keys())[0]
        self.computeAllFollows()
        parsing_table, result, tabTerm = self.createParseTable()
        if self.sample_input_string is not None:
            validity = self.validateStringUsingStackBuffer(parsing_table, result, tabTerm, self.sample_input_string)
            print(validity)
        else:
            print("\nNo input String detected")

# Exemplo de uso:
if __name__ == "__main__":
    rules = [
        "A -> S B | B",
        "S -> a | B c | #",
        "B -> b | d"
    ]
    nonterm_userdef = ['A', 'S', 'B']
    term_userdef = ['a', 'c', 'b', 'd']
    sample_input_string = "b c b"
    parser = Parser(rules, nonterm_userdef, term_userdef, sample_input_string)
    parser.run()
