import random as rand
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.shaders import lit_with_shadows_shader, basic_lighting_shader, unlit_shader, noise_fog_shader
from functools import partial
from panda3d.ai import AIWorld,AICharacter
#from ursina.editor.level_editor import LevelEditor
app = Ursina()

score = 0
bullet_list = []
enemy_list = []
shooting = True

class Enemy(Entity):
    def __init__(self,AiWorld,target, value = 5, **kwargs):
        super().__init__(model = 'cube',
                         scale = (2,4,2),
                         color = color.red,
                         collider = 'box',
                         **kwargs)
        self.AIchar = AICharacter("seeker",self.model, 100, 0.05, 5)

        AiWorld.addAiChar(self.AIchar)

        self.AIbehaviors = self.AIchar.getAiBehaviors()
        self.AIbehaviors.seek(target)

        self.value = value
        self.refreshing = False
        self.maxhealth = 100
        self.health = self.maxhealth

    def refresh(self):
        global score, score_text
        score += self.value
        self.visible = True
        self.collision = True
        self.health = self.maxhealth
        self.refreshing = False
        
    def update(self):
        if self.health<=0 and not self.refreshing:
            self.visible = False
            self.collision = False
            self.refreshing = True
            invoke(self.refresh, delay = 3)

class Bullet(Entity):
    def __init__(self, speed, damage, **kwargs):
        self.times = time.time()
        self.velocity = Vec3(0,0,0)
        super().__init__(model = 'sphere',
                           color = color.black,
                           scale = 0.1,
                           collider = 'sphere',
                           #ignore = ignore_list,
                           **kwargs)
        self.speed = speed
        self.damage = damage
        self.acceleration = Vec3(0, -9.81/9, 0)

    def update(self):
        global ignore_lise, enemy_list
        if time.time() - self.times >= 5:
            destroy(self)            
        elif self.intersects(ignore = ignore_list).hit == True:
            e_list = self.intersects(ignore = ignore_list).entities.copy()
            for i in e_list:
                if i in enemy_list:
                    i.health -= self.damage
            destroy(self)
        else:
            self.velocity += self.acceleration*time.dt
            self.velocity += self.acceleration*time.dt
            self.position += self.velocity*time.dt
            self.position += self.forward*self.speed*time.dt        
            
class Player(Entity):
    def __init__(self, **kwargs):
        global score
        self.controller = FirstPersonController(**kwargs)
        super().__init__(parent = self.controller)
        self.m4a1_gun = Entity(parent = self.controller.camera_pivot,
                               position = (0.7, -0.5, 1.3),
                               scale = 0.09,
                               rotation = (0, 180, 0),
                               model = 'map',
                               texture = 'weapon',
                               shader = basic_lighting_shader,
                               #always_on_top = True,
                               visible = False)
        self.shot_gun = Entity(parent = self.controller.camera_pivot,
                               position = (3, -0.5, 1.3),
                               rotation = (0, 180, 0),
                               scale = 0.25,
                               model = 'shotgun',
                               texture = 'shotgun',
                               model_center = (0,0,0),
                               #shader = basic_lighting_shader,
                               #always_on_top = True,
                               visible = True)
        '''elf.hand_gun = Entity(parent = self.controller.camera_pivot,
                               position = (0.7, -0.5, 1.3),
                               rotation = (0, 180, 0),
                               scale = 0.5,
                               model = 'USP',
                               texture = 'shotgun',
                               #shader = basic_lighting_shader,
                               #always_on_top = True,
                               visible = True)'''
        self.bulletcount = 1400
        self.maxmagcount = 20
        self.magcount = 20
        self.maxmagcounts = 5
        self.magcounts = 5
        self.current_weapon = 0
        self.shooting = False
        self.reloading = False
        self.weapons = [self.m4a1_gun, self.shot_gun, ]
        self.gun_pivot0 = Entity(parent = self.weapons[0],
                               position = (0,2.5,0),
                               visible = False)
        self.gun_pivot1 = Entity(parent = self.weapons[1],
                               position = (0,0,0),
                               visible = False)
        
        self.mag_text = Text(text = f'{self.magcount}', color = color.blue, origin = (-7, 12))
        
    def lerp_animation(self, g, v = 1):
        if self.current_weapon == 0:
            ofx = 1
            ofy = 0
        elif self.current_weapon == 1:
            ofx = 1
            ofy = 1
        g.shake(duration=.1, magnitude=0.2 * ofx, speed=.01, direction=(1,1*ofy), delay=0, attr_name='position', interrupt='finish')
        
    def shoot_animation(self):
        r = random.choice([-1,0,1])
        if held_keys['right mouse']:
            offset = 0.9
        else:
            offset = 1
        if self.current_weapon == 0:
            of = 1
        elif self.current_weapon == 1:
            of = 2.5
        self.controller.camera_pivot.rotation-=(1.4 * of ,0.5*offset*r,0)
        gun = self.weapons[self.current_weapon]
        invoke(partial(self.lerp_animation, gun), delay = (0.01))
        
    def startshooting(self):
        self.shooting = True
        self.shootingloop()

    def reload(self):
        if self.current_weapon == 0:
                self.bulletcount-=(self.maxmagcount-self.magcount)
                self.magcount = self.maxmagcount
        elif self.current_weapon == 1:
                self.bulletcount-=(self.maxmagcounts-self.magcounts)
                self.magcounts = self.maxmagcounts
        print('Reloaded', self.bulletcount)
        self.reloading = False
        
    def Shoot(self):
        self.shoot_animation()
        if held_keys['right mouse']:
            offset = 0.1
        else:
            offset = 0.2
        rx = random.randint(0,4) * offset
        ry = random.randint(0,4) * offset
        if self.current_weapon == 0:
            gun = self.gun_pivot0
            d = 15
            Bullet(speed = 350,
                   unlit = True,
                   damage = d,
                   position = gun.world_position,
                   rotation = self.controller.camera_pivot.world_rotation + (rx,ry,0))
        elif self.current_weapon == 1:
            gun = self.gun_pivot1
            d = 25
            a = 2
            Bullet(speed = 350,
                   unlit = True,
                   damage = d,
                   position = gun.world_position,
                   rotation = self.controller.camera_pivot.world_rotation + (rx,ry,0))
            Bullet(speed = 350,
                   unlit = True,
                   damage = d,
                   position = gun.world_position + (0.1,0.1,0),
                   rotation = self.controller.camera_pivot.world_rotation + (rx,ry,0) + (rx*a,ry*a,0))
            Bullet(speed = 350,
                   unlit = True,
                   damage = d,
                   position = gun.world_position + (-0.1,-0.1,0),
                   rotation = self.controller.camera_pivot.world_rotation + (rx,ry,0) + (-rx*a,-ry*a,0))
            Bullet(speed = 350,
                   unlit = True,
                   damage = d,
                   position = gun.world_position + (0.1,-0.1,0),
                   rotation = self.controller.camera_pivot.world_rotation + (rx,ry,0) + (rx*a,-ry*a,0))
            Bullet(speed = 350,
                   unlit = True,
                   damage = d,
                   position = gun.world_position + (-0.1,0.1,0),
                   rotation = self.controller.camera_pivot.world_rotation + (rx,ry,0)  + (-rx*a,ry*a,0))
            
    def shootingloop(self):
        if self.current_weapon == 0:
            if self.shooting and (self.magcount >= 1) and not self.reloading:
                self.Shoot()
                a = 0.11
                self.magcount -=1
                invoke(self.shootingloop, delay = a)#shooting delay
        elif self.current_weapon == 1:
            if self.shooting and (self.magcounts >= 1) and not self.reloading:
                self.Shoot()
                self.magcounts -=1
        if self.current_weapon == 0:
            if self.magcount<=0:
                self.reloading = True
                invoke(self.reload, delay = 3)
        elif self.current_weapon == 1:
            if self.magcounts<=0:
                self.reloading = True
                invoke(self.reload, delay = 2.5)

    def input(self, key):
        if key == 'left mouse down':
            self.startshooting()
            
        elif key == 'r':
            self.reloading = True
            if self.current_weapon == 0:
                invoke(self.reload, delay = 3)
            elif self.current_weapon == 1:
                invoke(self.reload, delay = 2.5)
            
        elif key == 'scroll up':
            if self.current_weapon != len(self.weapons)-1:
                self.current_weapon += 1
            else:
                self.current_weapon =0     
        elif key == 'scroll down':
            if self.current_weapon != 0:
                self.current_weapon -= 1
            else:
                self.current_weapon = len(self.weapons)-1   
        elif key == '1':
            self.current_weapon = 0
        elif key == '2':
            self.current_weapon = 1
        if self.reloading or (self.shooting == True and not held_keys['left mouse']):
            self.shooting = False

    def update(self):
        if self.current_weapon == 0:
            self.mag_text.text = f'{self.magcount}'
        elif self.current_weapon == 1:
            self.mag_text.text = f'{self.magcounts}'
        for ind, i in enumerate(self.weapons):
            if ind == self.current_weapon:
                i.visible = True
            else:
                i.visible = False
        gun = self.weapons[self.current_weapon]
        if held_keys['right mouse']:
            gun.x = lerp(gun.x, mouse.velocity.x, time.dt*5)
        else:
            gun.x = lerp(gun.x, mouse.velocity.x + 0.7, time.dt*2.5)
            gun.z = lerp(gun.z, mouse.velocity.z + 1, time.dt*2.5)

def update():
    score_text.text = f'Score {score}'

Entity.default_shader = basic_lighting_shader
Text.default_resolution = 1080 * Text.size

score_text = Text(text = f'Score {score}', color = color.yellow, origin = (0, -15))

Sky()
pivot = Entity()
light = DirectionalLight(parent = pivot, y = 2, x = 3, rotation = (45, -45, 45), shadows = True)
light.shadow_map_resolution = (1024, 1024)

ground1 = Entity(model='cube',
                scale=4,
                collider='box',
                texture='grass',
                shader = lit_with_shadows_shader,
                 position = (0,3,0))

#walls
wcolor =  color.rgb(255, 218, 185)
wall = Entity(model = 'cube',
              scale = (150,6,1),
              collider = 'box', color = wcolor,
              position = (0,2,75))

wall = Entity(model = 'cube',
              scale = (150,6,1),
              collider = 'box', color = wcolor,
              position = (0,2,-75))

wall = Entity(model = 'cube',
              scale = (1,6,150),
              collider = 'box', color = wcolor,
              position = (75,2,0))

wall = Entity(model = 'cube',
              scale = (1,6,150),
              collider = 'box', color = wcolor,
              position = (-75,2,0))

boundary_wall = Entity(model = 'cube',
              scale = (1,7,150),
              collider = 'box',
              color = rgb(255, 0, 0, 50),
              position = (25,2,0))



'''
ground = Entity(model='cube',
                scale=(120,1,120),
                collider='box',
                texture='grass',texture_scale = (10,10),
                shader = lit_with_shadows_shader,
                 position = (0,0,0))

ground = Entity(model='env',
                scale=1,
                collider='mesh',
                texture='env',)
                #shader = lit_with_shadows_shader)
'''

ground = Entity(model='map2',
                scale=1,
                collider='box',
                texture='dirt',)
                #shader = lit_with_shadows_shader)

#editor = LevelEditor()
for i in range(5):
    e = Enemy(position = (4+i*4, 3, 2))
    enemy_list.append(e)

player = Player(position = (0, 10, 0),
                speed = 10,
                mouse_sensitivity = Vec2(40, 40),
                gravity = 1,
                jump_up_duration = 0.7,
                air_time = 0.5,
                fall_after = .35,
                height = 2,
                jump_height = 4)

ignore_list = (boundary_wall, player)

app.run()
