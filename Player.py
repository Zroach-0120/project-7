from CollideObjectBase import SphereCollideObject
from panda3d.core import Loader, NodePath, Vec3, CollisionSphere, CollisionHandlerEvent, CollisionTraverser
from direct.task import Task
from direct.particles.ParticleEffect import ParticleEffect
import re
from direct.interval.LerpInterval import LerpFunc
from SpaceJamClasses import Missile

class Spaceship(SphereCollideObject):
    def __init__(self, loader, accept, modelPath, parentNode, nodeName, texPath, posVec, scaleVec, taskMgr, camera):
        super().__init__(loader, modelPath, parentNode, nodeName, posVec, scaleVec.x * 6)
        
        self.render = parentNode
        self.modelNode.setPos(posVec)
        self.modelNode.setScale(scaleVec)
        tex = loader.loadTexture(texPath)
        self.modelNode.setTexture(tex, 1)

        self.taskMgr = taskMgr
        self.camera = camera
        self.zoom_factor = 5
        self.cameraZoomSpeed = 10
        self.reloadTime = 0.25
        self.missileDistance = 4000
        self.missileBay = 1
        self.cntExplode = 0
        self.explodeIntervals = {}

        self.traverser = CollisionTraverser()
        self.handler = CollisionHandlerEvent()
        self.handler.addInPattern('into')
        accept('into', self.HandleInto)

        self.accept = accept
        self.freeCamera = False
        
        
        self.SetKeyBindings()
        self.taskMgr.add(self.UpdateCamera, "update-camera")
    def Fire(self):
        self.missile.Fire()

    def UpdateCamera(self, task):
        
        self.camera.reparentTo(self.modelNode)
        base.disableMouse()
        self.camera.setFluidPos(0, 1, 0)

    def SetKeyBindings(self):
        self.accept('w', self.move_forward, [1])    
        self.accept('w-up', self.move_forward, [0])  
        self.accept('a', self.turn_left, [1])       
        self.accept('a-up', self.turn_left, [0])     
        self.accept('d', self.turn_right, [1])      
        self.accept('d-up', self.turn_right, [0])    
        self.accept('s', self.turn_down, [1])       
        self.accept('s-up', self.turn_down, [0])     
        self.accept('q', self.roll_left, [1])       
        self.accept('q-up', self.roll_left, [0])     
        self.accept('e', self.roll_right, [1])      
        self.accept('e-up', self.roll_right, [0])    
        self.accept('z', self.zoom_out, [1])  
        self.accept('z-up', self.zoom_out, [0])
        self.accept('x', self.zoom_in, [1])  
        self.accept('x-up', self.zoom_in, [0])
        self.accept('f', self.Fire)
        #self.accept('c', self.ToggleFreeCamera)
        #self.accept('v', self.SwitchCameraView)
    
    #def ToggleFreeCamera(self):
        #self.freeCamera = not self.freeCamera
        #mode = "Free Camera" if self.freeCamera else "Following Camera"
        #print(f"{mode} enabled.")

    #def SwitchCameraView(self):
        #if not self.freeCamera:
            #self.currentCameraMode = (self.currentCameraMode + 1) % len(self.cameraModes)
            #print(f"Switched to {self.cameraModes[self.currentCameraMode]} view.")

    def zoom_in(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.ApplyZoomIn, 'zoom-in')
        else:
            self.taskMgr.remove('zoom-in')

    def ApplyZoomIn(self, task):
        self.camera.setPos(self.camera.getPos() + Vec3(0, self.cameraZoomSpeed, 0))
        return Task.cont

    def zoom_out(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.ApplyZoomOut, 'zoom-out')
        else:
            self.taskMgr.remove('zoom-out')

    def ApplyZoomOut(self, task):
        self.camera.setPos(self.camera.getPos() + Vec3(0, -self.cameraZoomSpeed, 0))
        return Task.cont

    def move_forward(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.ApplyMoveForward, 'move-forward')
        else:
            self.taskMgr.remove('move-forward')

    def ApplyMoveForward(self, task):
        rate = 5
        direction = self.modelNode.getQuat().getForward()
        self.modelNode.setPos(self.modelNode.getPos() + direction * rate)
        return Task.cont

    def turn_left(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.ApplyTurnLeft, 'turn-left')
        else:
            self.taskMgr.remove('turn-left')

    def ApplyTurnLeft(self, task):
        self.modelNode.setH(self.modelNode.getH() + 1.5)
        return Task.cont

    def turn_right(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.ApplyTurnRight, 'turn-right')
        else:
            self.taskMgr.remove('turn-right')

    def ApplyTurnRight(self, task):
        self.modelNode.setH(self.modelNode.getH() - 1.5)
        return Task.cont

    def turn_up(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.ApplyTurnUp, 'turn-up')
        else:
            self.taskMgr.remove('turn-up')

    def ApplyTurnUp(self, task):
        self.modelNode.setP(self.modelNode.getP() - 1.5)  # Upward tilt (pitch)
        return Task.cont

    def turn_down(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.ApplyTurnDown, 'turn-down')
        else:
            self.taskMgr.remove('turn-down')

    def ApplyTurnDown(self, task):
        self.modelNode.setP(self.modelNode.getP() + 1.5)  # Downward tilt (pitch)
        return Task.cont

    def roll_left(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.ApplyRollLeft, 'roll-left')
        else:
            self.taskMgr.remove('roll-left')

    def ApplyRollLeft(self, task):
        self.modelNode.setR(self.modelNode.getR() + 2.0)  # Roll left
        return Task.cont

    def roll_right(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.ApplyRollRight, 'roll-right')
        else:
            self.taskMgr.remove('roll-right')

    def ApplyRollRight(self, task):
        self.modelNode.setR(self.modelNode.getR() - 2.0)  # Roll right
        return Task.cont


    def HandleInto(self, entry):
        print("Collision detected!")
