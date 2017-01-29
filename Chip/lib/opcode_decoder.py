class Decoder:
    op_set = [
                               "00E0",
                               "00EE",
                               "1NNN",
                               "2NNN",
                               "3XNN",
                               "4XNN",
                               "5XNN",
                               "6XNN",
                               "7XNN",
                               "8XY0","8XY1","8XY2","8XY3","8XY4","8XY5",
                               "ANNN",
                               "CXNN",
                               "DXYN",
                               "EXA1",
                               "FX07","FX15","FX18","FX29","FX33","FX65"
                               ] # Editable from interpreter.

    def get_args(self,op,opcode):
        NNN = op.find("NNN")
        NN = op.find("NN")
        N = op.find("N")
        X = op.find("X")
        Y = op.find("Y")

        if NNN >= 0:
            NNN = True
        else:
            NNN = False

        if NN >= 0:
            NN = True
        else:
            NN = False

        if N >= 0:
            N = True
        else:
            N = False

        if X >= 0:
            X = True
        else:
            X = False

        if Y >= 0:
            Y = True
        else:
            Y = False
        
        if NNN:
            NN, N = False,False
        elif NN:
            NNN,N = False,False
        if N:
            NNN,NN = False,False

        if NNN:
            NNN = opcode[1:]
        else:
            NNN = None
        if NN:
            NN = opcode[2:]
        else:
            NN = None
        if N:
            N = opcode[3:]
        else:
            N = None
        if X:
            X = opcode[1]
        else:
            X = None
        if Y:
            Y = opcode[2]
        else:
            Y = None
        
        decoded = {"OPCODE":opcode,
                   "OP":op,
                   "NNN":NNN,
                   "NN":NN,
                   "N":N,
                   "X":X,
                   "Y":Y,
                   }
        return decoded
    
    def parse(self,opcode):
        if opcode.startswith("0x"):
            opcode = opcode[2:]
        if len(opcode) < 4:
            tmp = list(opcode)
            tmp.insert(0,"00")
            opcode = ''.join(tmp)
        opcode = opcode.upper()
        for op in self.op_set:
            error = False
            for i,char in enumerate(op):
                if char != opcode[i]:
                    if char not in "XYNxyn":
                        error = True
            if not error:
                return self.get_args(op,opcode)
"""
+=========================================+
#                                         #
#  O Example code & useage,               #
#                                         #
# 1. decoder = Decoder()                  #
# 2. print(decoder.parse("A204"))         #
#  O Output,                              #
# >>> 204                                 #
+=========================================+
"""

if __name__ == "__main__":
    decoder = Decoder()
    parse = decoder.parse("0x00ee")
    print(parse)
    # JUST FINISHED DECODER, ALL SYSTEMS GO!!!
