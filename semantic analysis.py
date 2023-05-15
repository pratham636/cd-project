def program():
    addScope(0)
    lex()
    if (tokenID == 'programtk'):
        lex()
        if (tokenID == 'idtk'):
            global program_name
            program_name = token
            lex()
            if (tokenID == '{'):
                lex()
                block(program_name)
            else:
                print("Error1: missing '{' in line " + str(line_num) + "!")
                sys.exit(-1)
            if (tokenID != '}'):
                print("Error2: missing '}' in line " + str(line_num) + "!")
                sys.exit(-1)
            lex()  # Should terminate the program by returning EOF
        else:
            print("Error3: program name expected in line " + str(line_num) + "!")
            sys.exit(-1)
    else:
        print("Error4: the keyword 'program' was expected in line " + str(line_num) + "!")
        sys.exit(-1)


def block(name):
    global programFramelength, programStartQuad, parSerialNum
    parSerialNum = 0  # reset parameters serial number for function/procedures in different nesting levels
    funcProc = None
    declarations()
    subprograms()
    # startQuad initialized for every function/Procedure
    if not (name == program_name):
        funcProc, nestLvl = searchEntity(name)
        funcProc.startQuad = nextquad()
    genquad("begin_block", name)
    statements()
    if (name == program_name):
        genquad("halt")
    genquad("end_block", name)
    # we are creating the framelengths for program, functions and procedures
    scope = scopeList[-1]
    if not (len(scope.entityList) == 0):
        varPar = None
        for i in range(len(scope.entityList) - 1, -1, -1):
            if (scope.entityList[i].entityType == "Variable" or scope.entityList[i].entityType == "TempVariable" or
                    scope.entityList[i].entityType == "Parameter"):
                varPar = scope.entityList[i]  # find the framelength of the last entity of the function/procedure
                break
        if not (varPar == None):
            if (name == program_name):
                programFramelength = varPar.offset + 4  # last function's/procedure's entity framelength+4
                scope.framelength = programFramelength  # store scopes framelength
            else:
                funcProc.framelength = varPar.offset + 4  # last function's/procedure's entity framelength+4
                scope.framelength = funcProc.framelength  # store scopes framelength
    else:
        funcProc.framelength = 12
        scope.framelength = funcProc.framelength
    print("###BEFORE DELETION###")
    printScopeList()
    if (funcProc == None):
        quad = programStartQuad  # programs starting quad
        while (1):
            if (quadList[quad][0] == "halt"):
                create_assembly_file(quad, program_name)
                break;
            create_assembly_file(quad,
                                 program_name)  # arguments are the quad we are working on(key of dictionary quadList) and the functions/procedures name we are in
            quad += 1
    else:
        quad = int(funcProc.startQuad)  # the quad that the function/procedure will start(quadList key)
        while (1):
            if (quadList[quad][0] == "end_block"):
                create_assembly_file(quad, funcProc.name)
                programStartQuad = quad + 1  # stores the quad that the program will start
                break;
            create_assembly_file(quad,
                                 funcProc.name)  # arguments are the quad we are working on(key of dictionary quadList) and the functions/procedures name we are in
            quad += 1
    if not (name == program_name):  # delete all but the 0 nesting level scopes
        deleteScope()  # because we need 0 nesting level for c code creation
        print("###AFTER DELETION###")
        printScopeList()
        print("####################################################################################")
    else:
        print("END OF SYMBOL TABLE!")


def declarations():
    while (tokenID == 'declaretk'):
        lex()
        varlist()
        scope = scopeList[-1]
        tempList = []
        for entity in scope.entityList:
            tempList.append(entity.name)
        if not (len(tempList) == len(set(tempList))):
            print("Error: Duplicated variable name declared on the same function/procedure in line " + str(
                line_num) + "!")
            sys.exit(1)
        del tempList
        if (tokenID == ';'):
            lex()
        else:
            print("Error5: Symbol ';' was expected in line " + str(line_num) + "!")
            sys.exit(-1)


def varlist():
    if (tokenID == 'idtk'):
        offset = scopeList[-1].framelength
        addVariable(token, "Variable", offset, scopeList[-1].entityList)
        scopeList[-1].framelength = scopeList[-1].entityList[-1].offset + 4
        lex()
        while (tokenID == ','):
            lex()
            if (tokenID == 'idtk'):
                offset = scopeList[-1].framelength
                addVariable(token, "Variable", offset, scopeList[-1].entityList)
                scopeList[-1].framelength = scopeList[-1].entityList[-1].offset + 4
                lex()
            else:
                print("Error6: Identifier expected after ',' not '" + token + "' in line " + str(line_num) + "!")
                sys.exit(-1)


def subprograms():
    while (tokenID == 'functiontk' or tokenID == 'proceduretk'):
        subprogram()


def subprogram():
    eType = tokenID
    lex()
    if (tokenID == 'idtk'):
        function_name = token
        if (eType == 'functiontk'):
            addFunction(function_name, "Function", scopeList[-1].entityList)
        else:
            addProcedure(function_name, "Procedure", scopeList[-1].entityList)
        scope = scopeList[-1]
        entity = scope.entityList[-1]
        for i in range(len(scope.entityList) - 1):
            if (scope.entityList[i].name == entity.name):
                print(
                    "Error: Duplicated name of " + entity.entityType + " with a variable in the same scope, line " + str(
                        line_num) + "!")
                # you can't name a function/procedure with the same name as a declaration, function or procedure in the same scope
                sys.exit(1)
        addScope(scopeList[-1].nestingLevel + 1)
        lex()
        funcbody(function_name)
    else:
        print("Error7: Expected function or procedure identifier in line " + str(line_num) + "!")
        sys.exit(-1)


def funcbody(funcName):
    formalpars()
    if (tokenID == '{'):
        lex()
        block(funcName)
    else:
        print("Error8: missing '{' in line " + str(line_num) + "!")
        sys.exit(-1)
    if (tokenID != '}'):
        print("Error9: missing '}' in line " + str(line_num) + "!")
        sys.exit(-1)
    lex()


def formalpars():
    if (tokenID == '('):
        lex()
        formalparlist()
    else:
        print("Error10: missing '(' in line " + str(line_num) + "!")
        sys.exit(-1)
    if (tokenID != ')'):
        print("Error11: missing ')' in line " + str(line_num) + "!")
        sys.exit(-1)
    lex()


def formalparlist():
    if not (tokenID == ')'):
        formalparitem()
        while (tokenID == ','):
            lex()
            formalparitem()


def formalparitem():
    if (tokenID == 'intk'):
        arg = addArgument(token, scopeList[-2].entityList[-1].argumentList)
        lex()
        if (tokenID == 'idtk'):
            offset = scopeList[-1].framelength
            addParameter(token, "Parameter", arg.mode, offset, scopeList[-1].entityList)
            scopeList[-1].framelength = scopeList[-1].entityList[-1].offset + 4
            lex()
        else:
            print(
                "Error12: Identifier(name) of variables expected instead of '" + token + "' after 'in' in line " + str(
                    line_num) + "!")
            sys.exit(1)
    elif (tokenID == 'inouttk'):
        arg = addArgument(token, scopeList[-2].entityList[-1].argumentList)
        lex()
        if (tokenID == 'idtk'):
            offset = scopeList[-1].framelength
            addParameter(token, "Parameter", arg.mode, offset, scopeList[-1].entityList)
            scopeList[-1].framelength = scopeList[-1].entityList[-1].offset + 4
            lex()
        else:
            print(
                "Error13: Identifier(name) of variables expected instead of '" + token + "' after 'inout' in line " + str(
                    line_num) + "!")
            sys.exit(1)
    else:
        print("Error14: 'in' or 'inout' expected instead of '" + token + "' in line " + str(line_num) + "!")
        sys.exit(1)


def statements():
    if (tokenID != '{'):
        statement()
    elif (tokenID == '{'):
        lex()
        statement()
        while (tokenID == ';'):
            lex()
            statement()
        if (tokenID != '}'):
            print("Error15: missing '}' in line " + str(line_num) + "!")
            sys.exit(-1)
        lex()


def statement():
    if (tokenID == 'idtk'):
        assignment_stat()
    elif (tokenID == 'iftk'):
        if_stat()
    elif (tokenID == 'whiletk'):
        while_stat()
    elif (tokenID == 'doublewhiletk'):
        doublewhile_stat()
    elif (tokenID == 'looptk'):
        loop_stat()
    elif (tokenID == 'exittk'):
        exit_stat()
    elif (tokenID == 'forcasetk'):
        forcase_stat()
    elif (tokenID == 'incasetk'):
        incase_stat()
    elif (tokenID == 'calltk'):
        call_stat()
    elif (tokenID == 'returntk'):
        return_stat()
    elif (tokenID == 'inputtk'):
        input_stat()
    elif (tokenID == 'printtk'):
        print_stat()


def assignment_stat():
    idname = token
    lex()
    if (tokenID == ':='):
        lex()
        exp = expression()
        genquad(":=", exp, "_", idname)
    else:
        print("Error16: ':=' expected instead of '" + token + "' in line " + str(line_num) + "!")
        sys.exit(1)


def if_stat():
    lex()
    if (tokenID == '('):
        lex()
        [Btrue, Bfalse] = condition()
    else:
        print("Error17: missing '(' in line " + str(line_num) + "!")
        sys.exit(-1)
    if (tokenID != ')'):
        print("Error18: missing ')' in line " + str(line_num) + "!")
        sys.exit(-1)
    lex()
    if (tokenID != 'thentk'):
        print("Error19: 'then' was expected instead of '" + token + "' in line " + str(line_num) + "!")
        sys.exit(-1)
    backpatch(Btrue, nextquad())
    lex()
    statements()
    ifList = makelist(nextquad())
    genquad("jump")
    backpatch(Bfalse, nextquad())
    elsepart()
    backpatch(ifList, nextquad())


def elsepart():
    if (tokenID == 'elsetk'):
        lex()
        statements()


def while_stat():
    lex()
    Bquad = nextquad()
    if (tokenID == '('):
        lex()
        [Btrue, Bfalse] = condition()
    else:
        print("Error20: missing '(' in line " + str(line_num) + "!")
        sys.exit(-1)
    if (tokenID != ')'):
        print("Error21: missing ')' in line " + str(line_num) + "!")
        sys.exit(-1)
    lex()
    backpatch(Btrue, nextquad())
    statements()
    genquad("jump", "_", "_", Bquad)
    backpatch(Bfalse, nextquad())


def doublewhile_stat():
    lex()
    if (tokenID == '('):
        lex()
        condition()
    else:
        print("Error22: missing '(' in line " + str(line_num) + "!")
        sys.exit(-1)
    if (tokenID != ')'):
        print("Error23: missing ')' in line " + str(line_num) + "!")
        sys.exit(-1)
    lex()
    statements()
    if (tokenID != 'elsetk'):
        print("Error24: 'else' was expected instead of '" + token + "' in line " + str(line_num) + "!")
        sys.exit(-1)
    lex()
    statements()


def loop_stat():
    lex()
    statements()


def exit_stat():
    lex()


def forcase_stat():
    lex()
    Fquad = nextquad()
    exitlist = emptylist()
    while (tokenID == 'whentk'):
        lex()
        if (tokenID == '('):
            lex()
            [condTrue, condFalse] = condition()
        else:
            print("Error25: missing '(' in line " + str(line_num) + "!")
            sys.exit(-1)
        if (tokenID != ')'):
            print("Error26: missing ')' in line " + str(line_num) + "!")
            sys.exit(-1)
        lex()
        if (tokenID != ':'):
            print("Error27: missing ':' in line " + str(line_num) + "!")
            sys.exit(-1)
        backpatch(condTrue, nextquad())
        lex()
        statements()
        Flist = makelist(nextquad())
        genquad("jump")
        exitlist = merge(exitlist, Flist)
        backpatch(condFalse, nextquad())
    if (tokenID != 'defaulttk'):
        print("Error28: 'default' was expected instead of '" + token + "' in line " + str(line_num) + "!")
        sys.exit(-1)
    lex()
    if (tokenID != ':'):
        print("Error29: missing ':' in line " + str(line_num) + "!")
        sys.exit(-1)
    lex()
    statements()
    backpatchQuad = str(int(nextquad()) + 1)
    backpatch(exitlist, backpatchQuad)
    exitQuad = str(int(nextquad()) + 2)
    genquad("jump", "_", "_", exitQuad)
    genquad("jump", "_", "_", Fquad)


def incase_stat():
    lex()
    while (tokenID == 'whentk'):
        lex()
        if (tokenID == '('):
            lex()
            condition()
        else:
            print("Error30: missing '(' in line " + str(line_num) + "!")
            sys.exit(-1)
        if (tokenID != ')'):
            print("Error31: missing ')' in line " + str(line_num) + "!")
            sys.exit(-1)
        lex()
        if (tokenID != ':'):
            print("Error32: missing ':' in line " + str(line_num) + "!")
            sys.exit(-1)
        lex()
        statements()


def return_stat():
    lex()
    exp = expression()
    genquad("retv", exp)


def call_stat():
    lex()
    if (tokenID == 'idtk'):
        call_name = token
        # code that checks the right calling of a Procedure
        entity, nstLvl = searchEntity(call_name)
        argList = []
        if (entity.entityType == "Procedure"):
            for arg in entity.argumentList:
                argList.append(arg.mode)
        lex()
        actualpars(argList)
        genquad("call", call_name)
    else:
        print("Error33: Identifier of a procedures name was expected instead of '" + token + "' in line " + str(
            line_num) + "!")
        sys.exit(1)


def print_stat():
    lex()
    if (tokenID == '('):
        lex()
        exp = expression()
        genquad("out", exp)
    else:
        print("Error34: missing '(' in line " + str(line_num) + "!")
        sys.exit(-1)
    if (tokenID != ')'):
        print("Error35: missing ')' in line " + str(line_num) + "!")
        sys.exit(-1)
    lex()


def input_stat():
    lex()
    if (tokenID == '('):
        lex()
        inputID = token
        if (tokenID == 'idtk'):
            genquad("inp", inputID)
            lex()
        else:
            print("Error36: Input(from keyboard) identifier was expected instead of '" + token + "' in line " + str(
                line_num) + "!")
            sys.exit(1)
    else:
        print("Error37: missing '(' in line " + str(line_num) + "!")
        sys.exit(-1)
    if (tokenID != ')'):
        print("Error38: missing ')' in line " + str(line_num) + "!")
        sys.exit(-1)
    lex()


def actualpars(argList):
    # argList is a list that contains the arguments that a calling function/procedure is assigned
    # actual_argList is a list that contains the arguments that the function/procedure we called actually defined when we created it
    if (tokenID == '('):
        lex()
        actual_argList = actualparlist()
        if (argList != actual_argList):
            print(
                "Error: Arguments assigned for this function/procedure are different from the ones we defined it with, in line " + str(
                    line_num) + "!")
            sys.exit(1)
    else:
        print("Error39: missing '(' in line " + str(line_num) + "!")
        sys.exit(-1)
    if (tokenID != ')'):
        print("Error40: missing ')' in line " + str(line_num) + "!")
        sys.exit(-1)
    lex()


def actualparlist():
    actual_argList = []
    if not (tokenID == ')'):
        a = actualparitem()
        actual_argList.append(a)
        while (tokenID == ','):
            lex()
            a = actualparitem()
            actual_argList.append(a)
    return actual_argList


def actualparitem():
    argType = ""
    if (tokenID == 'intk'):
        argType = "in"
        lex()
        par_item = expression()
        genquad("par", par_item, "CV")
    elif (tokenID == 'inouttk'):
        argType = "inout"
        lex()
        if (tokenID == 'idtk'):
            par_item = token
            genquad("par", par_item, "REF")
            lex()
        else:
            print("Error41: Identifier(name) of variable was expected instead of '" + token + "' in line " + str(
                line_num) + "!")
            sys.exit(1)
    else:
        print("Error42: Parameter type('in' or 'inout') expected instead of '" + token + "' in line " + str(
            line_num) + "!")
        sys.exit(1)
    return argType


def condition():
    [Q1true, Q1false] = boolterm()
    Btrue = Q1true
    Bfalse = Q1false
    while (tokenID == 'ortk'):
        backpatch(Bfalse, nextquad())
        lex()
        [Q2true, Q2false] = boolterm()
        Btrue = merge(Btrue, Q2true)
        Bfalse = Q2false
    return [Btrue, Bfalse]


def boolterm():
    [R1true, R1false] = boolfactor()
    Qtrue = R1true
    Qfalse = R1false
    while (tokenID == 'andtk'):
        backpatch(Qtrue, nextquad())
        lex()
        [R2true, R2false] = boolfactor()
        Qfalse = merge(Qfalse, R2false)
        Qtrue = R2true
    return [Qtrue, Qfalse]


def boolfactor():
    if (tokenID == 'nottk'):
        lex()
        if (tokenID == '['):
            lex()
            [Btrue, Bfalse] = condition()
        else:
            print("Error43: missing '[' in line " + str(line_num) + "!")
            sys.exit(-1)
        if (tokenID != ']'):
            print("Error44: missing ']' in line " + str(line_num) + "!")
            sys.exit(-1)
        Rtrue = Bfalse
        Rfalse = Btrue
        lex()
    elif (tokenID == '['):
        lex()
        [Btrue, Bfalse] = condition()
        if (tokenID != ']'):
            print("Error45: missing ']' in line " + str(line_num) + "!")
            sys.exit(-1)
        Rtrue = Btrue
        Rfalse = Bfalse
        lex()
    else:
        exp1 = expression()
        relop = relational_oper()
        exp2 = expression()
        Rtrue = makelist(nextquad())
        genquad(relop, exp1, exp2)
        Rfalse = makelist(nextquad())
        genquad("jump")
    return [Rtrue, Rfalse]


def expression():
    opsign = optional_sign()
    t1 = term()
    if (opsign == '+' or opsign == '-'):
        t1 = opsign + t1
    while (tokenID == '+' or tokenID == '-'):
        oper = token
        add_oper()
        t2 = term()
        w = newtemp()
        genquad(oper, t1, t2, w)
        t1 = w
    return t1


def term():
    f1 = factor()
    while (tokenID == '*' or tokenID == '/'):
        oper = token
        mul_oper()
        f2 = factor()
        w = newtemp()
        genquad(oper, f1, f2, w)
        f1 = w
    return f1


def factor():
    factor_value = token
    if (tokenID == 'consttk'):
        lex()
    elif (tokenID == '('):
        lex()
        exp = expression()
        factor_value = exp
        if (tokenID != ')'):
            print("Error46: missing ')' in line " + str(line_num) + "!")
            sys.exit(-1)
        lex()
    elif (tokenID == 'idtk'):
        lex()
        # code that checks the right calling of a Function
        entity, nstLvl = searchEntity(factor_value)
        argList = []
        if (entity.entityType == "Function"):
            for arg in entity.argumentList:
                argList.append(arg.mode)
        function_result = idtail(argList)
        # code that checks the right creation of a Function
        if (function_result == True):
            if not (entity.entityType == "Function"):
                print("Error: '" + entity.name + "' is not a function, line " + str(line_num) + "!")
                sys.exit(1)
            w = newtemp()
            genquad("par", w, "RET")
            genquad("call", factor_value)
            factor_value = w
        else:
            if (entity.entityType == "Function" or entity.entityType == "Procedure"):
                print("Error: '" + entity.name + "' is not a variable, line " + str(line_num) + "!")
                sys.exit(1)
    else:
        print("Error47: Constant or '(' or identifier missing in factor in line " + str(line_num) + "!")
        sys.exit(1)
    return factor_value


def idtail(argList):
    function_flag = False
    if (tokenID == '('):
        actualpars(argList)
        function_flag = True
    return function_flag


def relational_oper():
    relop = token
    if (tokenID == '='):
        lex()
    elif (tokenID == '<='):
        lex()
    elif (tokenID == '>='):
        lex()
    elif (tokenID == '>'):
        lex()
    elif (tokenID == '<'):
        lex()
    elif (tokenID == '<>'):
        lex()
    else:
        print("Error48: " + token + " causes an error in line " + str(line_num) + ".Relational operator expected!")
        sys.exit(-1)
    return relop


def add_oper():
    if (tokenID == '+'):
        lex()
    elif (tokenID == '-'):
        lex()
    else:
        print("Error49: " + token + " causes an error in line " + str(line_num) + ".Addition operator expected!")
        sys.exit(-1)


def mul_oper():
    if (tokenID == '*'):
        lex()
    elif (tokenID == '/'):
        lex()
    else:
        print("Error50: " + token + " causes an error in line " + str(line_num) + ".Multiplier operator expected!")
        sys.exit(-1)


def optional_sign():
    sign = token
    if (tokenID == '+' or tokenID == '-'):
        add_oper()
    return sign
