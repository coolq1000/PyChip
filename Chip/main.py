from lib import opcode_decoder
from _thread import *
import random,time,pygame,sys,numpy
import winsound

"""
+===============================================================+
#                                                               #
# + Credits,                                                    #
#  O Rohan Burke.                                               #
#                                                               #
# + Documentation,                                              #
#                                                               #
#  O Memory Map:                                                #
#   - 0x000 - 0x1FF : Reserved for interpreter.                 #
#   - 0x050 - 0x0A0 : System font set ( 4x5 pixels, 0-F ).      #
#   - 0x200 - 0xFFF : Program Rom and RAM.                      #
#                                                               #
+===============================================================+
"""

class cpu:

    def __init__(self,path,debug=False,cap="Chip-8 Emulator"):
        """
            Reset machine.
        """

        # Initialize Pygame,
        pygame.init()

        # Difine width,hieght resolutions,
        self.w,self.h = 256,128
        self.screen = pygame.display.set_mode((self.w,self.h))

        pygame.display.set_caption(str(cap))
        
        
        # Create Decoder.
        self.decoder = opcode_decoder.Decoder()

        self.decoder.op_set = [
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
                               ]
        
        self.running = True
        self.debug = debug
        
        """
         Partition 4096/4K RAM as list. Technically it's 16K for every int in
         Python is 4 bytes long, whereas the chip-8 has only 1 byte long memory locations.
        """
        self.memory = [0]*4096
        self.V = [0]*16

        self.stack = []

        self.dt = 0
        self.st = 0

        self.pc = 0x200
        self.opcode = 0
        self.index = 0

        # Create a system font (0-F).
        self.sys_font = [0xF0, 0x90, 0x90, 0x90, 0xF0,
                         0x20, 0x60, 0x20, 0x20, 0x70,
                         0xF0, 0x10, 0xF0, 0x80, 0xF0,
                         0xF0, 0x10, 0xF0, 0x10, 0xF0,
                         0x90, 0x90, 0xF0, 0x10, 0x10,
                         0xF0, 0x80, 0xF0, 0x10, 0xF0,
                         0xF0, 0x80, 0xF0, 0x90, 0xF0,
                         0xF0, 0x10, 0x20, 0x40, 0x40,
                         0xF0, 0x90, 0xF0, 0x90, 0xF0,
                         0xF0, 0x90, 0xF0, 0x10, 0xF0,
                         0xF0, 0x90, 0xF0, 0x90, 0x90,
                         0xE0, 0x90, 0xE0, 0x90, 0xE0,
                         0xF0, 0x80, 0x80, 0x80, 0xF0,
                         0xE0, 0x90, 0x90, 0x90, 0xE0,
                         0xF0, 0x80, 0xF0, 0x80, 0xF0,
                         0xF0, 0x80, 0xF0, 0x80, 0x80
                       ]

        self.gfx = [[0 for x in range(64)] for y in range(32)] # 64x32 screen.

        self.keys = [0]*16  # x16 hex keyboard.

        # Load/Dump font at self.memory[0x00]
        for i,char in enumerate(self.sys_font):
            self.memory[i] = char

        self.main(path)
    
    def log(self,message,end="\n"):
        """
            Same as print, except with this we can disable it easily.
        """
        if self.debug:
            print(message,end=end)
    
    def main(self,path):
        """
            Main loop.
        """
        self.load(path)
        
        while self.running:
            self.cycle()

    def load(self,path):
        self.log("Loading ROM {0}".format(path))
        binary = open(path,'rb').read()

        for i,byte in enumerate(binary):
            # Load/Dump ROM at 0x200
            self.memory[0x200+i] = byte
        self.log("Loaded.")

    def beep(self):
        # Play sound.
        Freq = 750
        Dur = 100
        winsound.Beep(Freq,Dur)

    count = 0
    def cycle(self):
        self.key = pygame.key.get_pressed()

        if self.key[pygame.K_h]:
            if not self.debug:
                setto = True
            elif self.debug:
                setto = False
            if setto:
                self.debug = True
            else:
                self.debug = False
        
        if pygame.event.poll().type == pygame.QUIT: pygame.quit(); sys.exit()

        self.count += 1
        self.skip = 10
        if self.key[pygame.K_SPACE]: self.skip *= 50
        if self.count % self.skip == 0:
            for y in range(32):
                for x in range(64):
                    if self.gfx[y][x]:
                        self.screen.fill((255,255,255),(x*self.w/64,y*self.h/32,1*self.w/64,1*self.h/32))
                    else:
                        self.screen.fill((0,0,0),(x*self.w/64,y*self.h/32,1*self.w/64,1*self.h/32))
            pygame.display.flip()
        self.log("-------------------------------")
        #self.log("OPCODE: 0x"+hex(self.opcode).upper()[2:])
        self.log("DISC: ",end="")
        oldPC = self.pc
        self.process_opcode()
        self.log("FUNC: _"+hex(self.opcode).upper()[2:]+"()")
        self.log("PC: hex("+hex(oldPC)+" > "+hex(self.pc)+"), int("+str(oldPC)+" > "+str(self.pc)+").")
        self.log("DT: "+str(self.dt))
        self.log("ST: "+str(self.st))
        self.log("Registers: {0}".format(self.V))
        self.log("Index: {0}".format(hex(self.index)))
        if self.dt > 0:
            self.dt -= 1
        if self.st > 0:
            self.st -= 1
            if self.st == 0:
                # Play sound.
                start_new_thread(self.beep,())
                pass

    def process_opcode(self):
        # Load opcode at self.memory[self.pc],
        self.opcode = self.memory[self.pc]
        
        # Merge with next byte,
        self.opcode <<= 8
        self.opcode |= self.memory[self.pc+1]

        # Run function according to decoded opcode,
        parse = self.decoder.parse(hex(self.opcode))
        
        if parse == None:
            print("Couldn't decode opcode, "+hex(self.opcode))
            self.pc += 2
        elif hasattr(self,"_"+parse["OP"]):
            toCall = getattr(self,"_"+parse["OP"])
            toCall(parse)
        else:
            print("Unknown opcode, "+hex(self.opcode)+" _"+parse["OP"])
            self.pc += 2
    def _00E0(self,args):
        #
        #   Clear screen.
        #
        self.gfx = [[0 for x in range(64)] for y in range(32)]
        self.screen.fill((0,0,0))
        self.pc += 2
        self.log("_00"+hex(self.opcode).upper()[2:]+" Clear screen.")
    
    def _00EE(self,args):
        #
        #   Return from subroutine.
        #
        self.pc = self.stack.pop()
        self.pc += 2
        self.log("_00"+hex(self.opcode).upper()[2:]+" Return from subroutine.")

    def _1NNN(self,args):
        #
        #   Jump to NNN.
        #
        NNN = int(args["NNN"],16)
        self.pc = NNN
        self.log("_"+hex(self.opcode).upper()[2:]+" Jump to NNN.")

    def _2NNN(self,args):
        #
        #   Call subroutine at NNN.
        #
        NNN = int(args["NNN"],16)
        self.stack.append(self.pc)
        self.pc = NNN
        self.log("_"+hex(self.opcode).upper()[2:]+" Call subroutine at NNN.")

    def _3XNN(self,args):
        #
        #   Skip next instruction if VX == NN.
        #
        X = int(args["X"],16)
        NN = int(args["NN"],16)
        
        if self.V[X] == NN:
            self.pc += 4
        else:
            self.pc += 2
        self.log("_"+hex(self.opcode).upper()[2:]+" Skip next instruction if VX == NN.")

    def _4XNN(self,args):
        #
        #   Skip next instruction if VX != NN.
        #

        X = int(args["X"],16)
        NN = int(args["NN"],16)
        
        if self.V[X] != NN:
            self.pc += 4
        else:
            self.pc += 2
        self.log("_"+hex(self.opcode).upper()[2:]+" Skip next instruction if VX != NN.")

    def _6XNN(self,args):
        #
        #   VX := NN.
        #
        X = int(args["X"],16)
        NN = int(args["NN"],16)
        
        self.V[X] = NN
        self.pc += 2
        self.log("_"+hex(self.opcode).upper()[2:]+" VX := NN.")

    def _7XNN(self,args):
        #
        #   VX += VX + NN.
        #
        X = int(args["X"],16)
        NN = int(args["NN"],16)
        
        self.V[X] += NN
        self.pc += 2
        self.log("_"+hex(self.opcode).upper()[2:]+" VX += VX + NN.")

    def _8XY0(self,args):
        #
        #   VX = VY.
        #
        X = int(args["X"],16)
        Y = int(args["Y"],16)
        
        self.V[X] = self.V[Y]
        self.pc += 2
        self.log("_"+hex(self.opcode).upper()[2:]+" VX = VY.")

    def _8XY2(self,args):
        #
        #   VX &= VY.
        #
        X = int(args["X"],16)
        Y = int(args["Y"],16)
        
        self.V[X] &= self.V[Y]
        self.pc += 2
        self.log("_"+hex(self.opcode).upper()[2:]+" VX &= VY.")

    def _8XY3(self,args):
        #
        #   VX ^= VY
        #
        X = int(args["X"],16)
        Y = int(args["Y"],16)
        
        self.V[X] ^= self.V[Y]
        self.pc += 2
        self.log("_"+hex(self.opcode).upper()[2:]+" VX ^= VY.")

    def _8XY4(self,args):
        #
        #   VX += VY. VF := carry.
        #
        X = int(args["X"],16)
        Y = int(args["Y"],16)

        vx,vy = self.V[X],self.V[Y]

        vz = vx+vy

        self.V[X] = vz % 0x100

        if vz > 0xFF:
            self.V[0xF] = 1
        else:
            self.V[0xF] = 0
        self.pc += 2
        self.log("_"+hex(self.opcode).upper()[2:]+" VX += VY. VF := carry.")

    def _8XY5(self,args):
        #
        #   VX -= VY. VF := !borrow.
        #
        X = int(args["X"],16)
        Y = int(args["Y"],16)

        vx,vy = self.V[X],self.V[Y]

        vz = vx-vy

        if vz < 0:
            self.V[X] = vz + 0x100
        else:
            self.V[X] = vz

        if vz < 0:
            self.V[0xF] = 0
        else:
            self.V[0xF] = 1
        self.pc += 2
        self.log("_"+hex(self.opcode).upper()[2:]+" VX := VY. VF := !borrow.")

    def _ANNN(self,args):
        #
        #   I := NNN.
        #
        NNN = int(args["NNN"],16)

        self.index = NNN
        self.pc += 2
        self.log("_"+hex(self.opcode).upper()[2:]+" I := NNN.")


    def _CXNN(self,args):
        #
        #   VX := rand(0,0xFF) & NN.
        #
        X = int(args["X"],16)
        NN = int(args["NN"],16)

        rand = random.randint(0,0xFF)
        self.V[X] = rand & NN
        self.pc += 2
        self.log("_"+hex(self.opcode).upper()[2:]+" VX := rand(0,0xFF) & NN.")

    def _DXYN(self,args):
        #
        #   draw(X,Y,N).
        #
        X = int(args["X"],16)
        Y = int(args["Y"],16)
        N = int(args["N"],16)
        
        spr_bytes = self.memory[self.index:self.index+N]
        sprite = numpy.zeros((N,8), numpy.bool)
        for y in range(N):
            for x in range(8):
                rx = 7 - x
                if self.get_bit(spr_bytes[y],rx) == 1:
                    sprite[y][x] = 1
        
        self.V[0xF] = 0

        for y in range(N):
            for x in range(8):
                if sprite[y][x] == 1:
                    sy = self.V[Y] + y
                    sx = self.V[X] + x

                    sh,sw = 32,64
                    if sy < sh and sx < sw:
                        if self.gfx[sy][sx] == 1:
                            self.V[0xF] = 1
                        self.gfx[sy][sx] ^= 1
        
        self.pc += 2
        self.log("_"+hex(self.opcode).upper()[2:]+" draw(X,Y,N).")

    def _EXA1(self,args):
        #
        #   Skip next instruction if key VX is not pressed.
        #
        X = int(args["X"],16)

        # I have momentarially swapped Q and E!!!

        keymap = [self.key[pygame.K_1],
                  self.key[pygame.K_2],
                  self.key[pygame.K_3],
                  self.key[pygame.K_4],
                  self.key[pygame.K_e],
                  self.key[pygame.K_w],
                  self.key[pygame.K_q],
                  self.key[pygame.K_r],
                  self.key[pygame.K_a],
                  self.key[pygame.K_s],
                  self.key[pygame.K_d],
                  self.key[pygame.K_f],
                  self.key[pygame.K_z],
                  self.key[pygame.K_x],
                  self.key[pygame.K_c],
                  self.key[pygame.K_v]]
        count = 0
        while count < len(keymap):
            self.keys[count] = keymap[count]
            count += 1

        if self.keys[self.V[X]] == 1:
            self.pc += 4
        else:
            self.pc += 2

        self.log("_"+hex(self.opcode).upper()[2:]+" Skip next instruction if key VX is not pressed.")

    def _FX07(self,args):
        #
        #   VX := dt.
        #
        X = int(args["X"],16)

        self.V[X] = self.dt
        self.pc += 2
        self.log("_"+hex(self.opcode).upper()[2:]+" VX := dt.")

    def _FX15(self,args):
        #
        #   dt := VX.
        #
        X = int(args["X"],16)

        self.dt = self.V[X]
        self.pc += 2
        self.log("_"+hex(self.opcode).upper()[2:]+" dt := VX.")

    def _FX18(self,args):
        #
        #   st := VX.
        #
        X = int(args["X"],16)

        self.st = self.V[X]
        self.pc += 2
        self.log("_"+hex(self.opcode).upper()[2:]+" st := VX.")

    def _FX29(self,args):
        #
        #   Point I to 5 byte font for hex char VX.
        #
        X = int(args["X"],16)

        self.index = self.V[X]*5
        self.pc += 2
        self.log("_"+hex(self.opcode).upper()[2:]+" Point I to 5 byte font for hex char VX.")

    def _FX33(self,args):
        #
        #   Store BCD representation of VX in M[index] to M[index+2]
        #
        X = int(args["X"],16)

        self.memory[self.index] = self.V[X] // 100 % 10
        self.memory[self.index+1] = self.V[X] // 10 % 10
        self.memory[self.index+2] = self.V[X] % 10
        self.pc += 2
        self.log("_"+hex(self.opcode).upper()[2:]+" Store BCD of VX in M.")

    def _FX65(self,args):
        #
        #   Read V[0x0] to VX from memory at M[index].
        #
        X = int(args["X"],16)

        for i in range(X+1):
            self.V[i] = self.memory[self.index+i]
        self.pc += 2
        self.log("_"+hex(self.opcode).upper()[2:]+" Read memory at VX.")

    def get_bit(self,s,ri):
        m = 0x1 << ri
        return (s&m)>>ri

if __name__ == "__main__":
    processor = cpu("roms/BREAKOUT",debug=False)
