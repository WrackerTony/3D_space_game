from ursina import *
from random import uniform, choice, random

app = Ursina()

window.title = '3D Space Runner'
window.borderless = False
window.fullscreen = False
window.exit_button.visible = False
window.fps_counter.enabled = True

game_running = True

# Available meteorite models (working OBJ files)
meteorite_models = [
    {
        'model': 'meteorit_style/meteorit.obj',
        'texture': 'meteorit_style/meteorit.png'
    }
]

# Player ship
class Player(Entity):
    def __init__(self, **kwargs):
        super().__init__(
            model='Cool_Space_ship__0623175827_texture.obj',
            texture='Cool_Space_ship__0623175827_texture.png',
            color=color.white,  # fallback color
            scale=(0.5, 0.2, 1),
            position=(0, 0, 0),
            **kwargs
        )
        self.speed = 3.5
        self.forward_speed = 12  # increased speed
        self.velocity = Vec3(0, 0, 0)
        self.target_rotation_x = 0
        self.target_rotation_z = 0

player = Player()

camera.position = (0, 2, -10)
camera.rotation = (10, 0, 0)

# Obstacle class
class Obstacle(Entity):
    def __init__(self, **kwargs):
        # Randomly choose a meteorite model
        meteorite = choice(meteorite_models)
        # Randomize meteorite size (scale) - much smaller and more reasonable
        base_scale = uniform(0.3, 1.2)  # Base scale between 0.3 and 0.8
        random_scale = (base_scale, base_scale, base_scale)  # Keep proportions
        self.collision_radius = base_scale * 0.5  # Store collision radius based on scale
        
        if meteorite['texture']:
            super().__init__(
                model=meteorite['model'],
                texture=meteorite['texture'],
                color=color.white,
                scale=random_scale,
                position=(uniform(-4,4), uniform(-3,3), player.z + uniform(50,80)),
                **kwargs
            )
        else:
            super().__init__(
                model=meteorite['model'],
                color=color.gray,
                scale=random_scale,
                position=(uniform(-4,4), uniform(-3,3), player.z + uniform(50,80)),
                **kwargs
            )
    def update(self):
        if self.z < player.z - 5:
            destroy(self)
            return True  # Mark for removal
        return False

obstacles = []
spawn_timer = 0
spawn_interval = 1.2  # restore original spawn interval

def spawn_obstacle():
    obstacle = Obstacle()
    obstacles.append(obstacle)

def check_collision(player, obstacle):
    # Dynamic hitbox based on meteorite size
    distance = (player.position - obstacle.position).length()
    collision_threshold = obstacle.collision_radius + 0.3  # Obstacle radius + small player radius
    return distance < collision_threshold

# --- Step 2 additions: Energy Orbs, Power Bar, Scoring ---
class EnergyOrb(Entity):
    def __init__(self, orb_type='power', **kwargs):
        self.orb_type = orb_type
        color_map = {
            'power': color.lime,
            'speed_up': color.rgb(128,0,255),
            'slow_down': color.azure,
            'shooter': color.red
        }
        orb_color = color_map.get(orb_type, color.lime)
        if 'position' not in kwargs:
            kwargs['position'] = (uniform(-4,4), uniform(-3,3), player.z + uniform(50,80))
        super().__init__(
            model='sphere',
            color=orb_color,
            scale=0.4,
            **kwargs
        )
    def update(self):
        if self.z < player.z - 20:
            destroy(self)
            return True
        return False

energy_orbs = []
orbs_collected = 0
orb_spawn_timer = 0
orb_spawn_interval = 1.8

power = 1.0  # 1.0 = full, 0.0 = empty
power_depletion_rate = 0.06  # per second, slower depletion for longer bar
power_orb_value = 0.25

# Orb spawn logic with rarity
orb_types = ['power', 'speed_up', 'slow_down', 'shooter']
last_special_orb_distance = 0
def choose_orb_type(force_shooter=False):
    if force_shooter:
        return 'shooter'
    r = random()
    if r < 0.7:
        return 'power'      # 70% chance
    elif r < 0.85:
        return 'speed_up'   # 15% chance
    elif r < 0.99:
        return 'slow_down'  # 14% chance
    else:
        return 'shooter'    # 1% chance (very rare)

def spawn_energy_orb():
    global last_special_orb_distance
    force_shooter = False
    # Guarantee a red orb every 1000 distance
    if int(player.z // 1000) > int(last_special_orb_distance // 1000):
        force_shooter = True
        last_special_orb_distance = player.z
    orb_type = choose_orb_type(force_shooter=force_shooter)
    orb = EnergyOrb(orb_type=orb_type)
    energy_orbs.append(orb)

def check_orb_collision(player, orb):
    distance = (player.position - orb.position).length()
    return distance < 0.6

# UI
score_text = Text(text='Score: 0', position=(-0.85,0.45), scale=1.5, background=True)
distance_text = Text(text='Distance: 0', position=(-0.85,0.4), scale=1.2, background=True)
power_bar_bg = Entity(parent=camera.ui, model='quad', color=color.gray, scale=(0.4,0.03), position=(0,0.43))
power_bar = Entity(parent=camera.ui, model='quad', color=color.green, scale=(0.39,0.02), position=(0,0.43))

# --- Step 3: Menus, Help, and Game State ---
game_state = 'start'  # can be 'start', 'playing', 'gameover', 'help'
menu_panel = None
help_panel = None

def clear_all_ui():
    """Clear all UI elements to prevent overlapping"""
    global menu_panel, help_panel, game_over_panel
    if menu_panel:
        destroy(menu_panel)
        menu_panel = None
    if help_panel:
        destroy(help_panel)
        help_panel = None
    if game_over_panel:
        destroy(game_over_panel)
        game_over_panel = None

def show_start_menu():
    global menu_panel, game_state
    clear_all_ui()
    game_state = 'start'
    
    # Create a larger, more prominent background
    menu_panel = Entity(
        parent=camera.ui, 
        model='quad', 
        color=color.rgba(0, 0, 0, 0.85), 
        scale=(0.9, 0.7), 
        position=(0, 0, 0)
    )
    
    # Main title with better styling
    Text(
        parent=menu_panel, 
        text='3D SPACE RUNNER', 
        y=0.25, 
        scale=3.5, 
        origin=(0, 0), 
        color=color.cyan
    )
    
    # Subtitle
    Text(
        parent=menu_panel, 
        text='Navigate through space, collect energy orbs, and survive!', 
        y=0.15, 
        scale=1.2, 
        origin=(0, 0), 
        color=color.light_gray
    )
    
    # Start Game button
    start_btn = Button(
        text='START GAME', 
        parent=menu_panel, 
        y=0.02, 
        scale=(0.5, 0.12), 
        text_scale=1.5,
        on_click=start_game
    )
    start_btn.color = color.azure
    start_btn.text_color = color.white
    
    # Help button
    help_btn = Button(
        text='HELP & CONTROLS', 
        parent=menu_panel, 
        y=-0.12, 
        scale=(0.5, 0.12), 
        text_scale=1.3,
        on_click=show_help
    )
    help_btn.color = color.orange
    help_btn.text_color = color.white
    
    # Credits
    Text(
        parent=menu_panel, 
        text='Created by Wracker', 
        y=-0.25, 
        scale=1.1, 
        origin=(0, 0), 
        color=color.gray
    )
    
    # Version info
    Text(
        parent=menu_panel, 
        text='v1.0 - Space Adventure Game', 
        y=-0.30, 
        scale=0.9, 
        origin=(0, 0), 
        color=color.dark_gray
    )

def hide_start_menu():
    global menu_panel
    if menu_panel:
        destroy(menu_panel)
        menu_panel = None

def show_help():
    global help_panel, game_state
    clear_all_ui()
    game_state = 'help'
    
    help_panel = Entity(
        parent=camera.ui, 
        model='quad', 
        color=color.rgba(0, 0, 0, 0.9), 
        scale=(0.9, 0.8), 
        position=(0, 0, -1)
    )
    
    # Help title
    Text(
        parent=help_panel, 
        text='GAME CONTROLS & HELP', 
        y=0.36, 
        scale=2.5, 
        origin=(0, 0), 
        color=color.yellow
    )
    
    # Short intro
    Text(
        parent=help_panel,
        text='Survive as long as you can! Dodge meteorites, collect orbs, and keep your power up.',
        y=0.29,
        scale=1.1,
        origin=(0,0),
        color=color.white
    )
    
    # Movement controls
    Text(
        parent=help_panel, 
        text='MOVEMENT:', 
        y=0.22, 
        scale=1.6, 
        origin=(0, 0), 
        color=color.cyan
    )
    Text(
        parent=help_panel, 
        text='W/S: Move Up/Down    A/D: Move Left/Right', 
        y=0.16, 
        scale=1.2, 
        origin=(0, 0), 
        color=color.white
    )
    
    # Orb types (moved up, no emoji)
    Text(
        parent=help_panel, 
        text='ORB TYPES:', 
        y=0.09, 
        scale=1.5, 
        origin=(0, 0), 
        color=color.orange
    )
    Text(
        parent=help_panel, 
        text='Green Power Orb: Restores your energy bar', 
        y=0.04, 
        scale=1.1, 
        origin=(0, 0), 
        color=color.lime
    )
    Text(
        parent=help_panel, 
        text='Purple Speed Up Orb: Temporarily increases speed', 
        y=-0.01, 
        scale=1.1, 
        origin=(0, 0), 
        color=color.rgb(180,100,255)
    )
    Text(
        parent=help_panel, 
        text='Blue Slow Down Orb: Temporarily decreases speed', 
        y=-0.06, 
        scale=1.1, 
        origin=(0, 0), 
        color=color.azure
    )
    Text(
        parent=help_panel, 
        text='Red Shooter Orb: Enables shooting mode for 10s', 
        y=-0.11, 
        scale=1.1, 
        origin=(0, 0), 
        color=color.red
    )
    
    # Gameplay section (moved up)
    Text(
        parent=help_panel, 
        text='GAMEPLAY:', 
        y=-0.18, 
        scale=1.5, 
        origin=(0, 0), 
        color=color.lime
    )
    Text(
        parent=help_panel, 
        text='• Avoid meteorites\n• Collect energy orbs\n• Maintain your power bar\n• Use Space to shoot (when red orb is active)', 
        y=-0.25, 
        scale=1.1, 
        origin=(0, 0), 
        color=color.white
    )
    
    # Back button
    back_btn = Button(
        text='BACK TO MENU', 
        parent=help_panel, 
        y=-0.36, 
        scale=(0.4, 0.1), 
        text_scale=1.2,
        on_click=back_to_menu
    )
    back_btn.color = color.azure
    back_btn.text_color = color.white

def hide_help():
    global help_panel
    if help_panel:
        destroy(help_panel)
        help_panel = None

def back_to_menu():
    global game_state
    hide_help()
    show_start_menu()
    game_state = 'start'

def start_game():
    global game_state
    clear_all_ui()
    restart_game()
    game_state = 'playing'

game_over_panel = None

def show_game_over():
    global game_over_panel, game_state
    clear_all_ui()
    game_state = 'gameover'
    
    game_over_panel = Entity(
        parent=camera.ui, 
        model='quad', 
        color=color.rgba(0, 0, 0, 0.9), 
        scale=(0.8, 0.6), 
        position=(0, 0, 0)
    )
    
    # Game Over title
    Text(
        parent=game_over_panel, 
        text='GAME OVER!', 
        y=0.2, 
        scale=3, 
        origin=(0, 0), 
        color=color.red
    )
    
    # Stats
    Text(
        parent=game_over_panel, 
        text=f'Energy Orbs Collected: {orbs_collected}', 
        y=0.08, 
        scale=1.6, 
        origin=(0, 0), 
        color=color.lime
    )
    
    Text(
        parent=game_over_panel, 
        text=f'Distance Traveled: {int(player.z)} units', 
        y=0.02, 
        scale=1.4, 
        origin=(0, 0), 
        color=color.cyan
    )
    
    # Buttons
    play_again_btn = Button(
        text='PLAY AGAIN', 
        parent=game_over_panel, 
        y=-0.08, 
        scale=(0.4, 0.1), 
        text_scale=1.3,
        on_click=start_game
    )
    play_again_btn.color = color.azure
    play_again_btn.text_color = color.white
    main_menu_btn = Button(
        text='MAIN MENU', 
        parent=game_over_panel, 
        y=-0.18, 
        scale=(0.4, 0.1), 
        text_scale=1.3,
        on_click=back_to_menu
    )
    main_menu_btn.color = color.orange
    main_menu_btn.text_color = color.white

def hide_game_over():
    global game_over_panel
    if game_over_panel:
        destroy(game_over_panel)
        game_over_panel = None

# --- Shooting mechanic ---
shooting_mode = False
shooting_timer = 0
projectiles = []

class Projectile(Entity):
    def __init__(self, **kwargs):
        super().__init__(
            model='cube',
            color=color.orange,
            scale=(0.1, 0.1, 0.6),
            position=player.position + Vec3(0, 0, 1.5),
            rotation=player.rotation,
            **kwargs
        )
        self.speed = 60
        self._destroyed = False
    def update(self):
        if self._destroyed:
            return True
        self.z += self.speed * time.dt
        # Remove if too far
        if self.z > player.z + 100:
            destroy(self)
            self._destroyed = True
            return True
        # Check collision with obstacles
        for obstacle in obstacles[:]:
            if (self.position - obstacle.position).length() < (obstacle.collision_radius + 0.2):
                shatter_meteorite(obstacle)
                if obstacle in obstacles:
                    obstacles.remove(obstacle)
                destroy(self)
                self._destroyed = True
                return True
        return False

def shatter_meteorite(meteorite):
    # Simple shatter animation: scale down and fade out
    meteorite.animate_scale(Vec3(0,0,0), duration=0.4, curve=curve.in_expo)
    meteorite.animate_color(color.clear, duration=0.4)
    invoke(destroy, meteorite, delay=0.45)

def input(key):
    global game_running, game_state, shooting_mode, projectiles
    if game_state == 'gameover' and key == 'r':
        start_game()
    if game_state == 'start' and key == 'enter':
        start_game()
    if game_state == 'help' and key == 'escape':
        back_to_menu()
    # Shooting
    if game_state == 'playing' and shooting_mode and key == 'space':
        proj = Projectile()
        projectiles.append(proj)

def restart_game():
    global game_running, obstacles, energy_orbs, orbs_collected, power, player, spawn_timer, orb_spawn_timer, game_state
    clear_all_ui()
    for o in obstacles:
        destroy(o)
    for e in energy_orbs:
        destroy(e)
    obstacles.clear()
    energy_orbs.clear()
    player.x = 0
    player.y = 0
    player.z = 0
    player.velocity = Vec3(0,0,0)
    orbs_collected = 0
    power = 1.0
    spawn_timer = 0
    orb_spawn_timer = 0
    game_running = True
    application.paused = False
    # Spawn a red shooter orb at the start
    shooter_orb = EnergyOrb(orb_type='shooter', position=(0, 0, 15))
    energy_orbs.append(shooter_orb)

# Update function
def update():
    global spawn_timer, game_running, obstacles, orb_spawn_timer, energy_orbs, orbs_collected, power, spawn_interval, game_state
    global shooting_mode, shooting_timer, projectiles
    if game_state != 'playing':
        return
    hide_game_over()
    # Difficulty scaling
    # Increase speed and spawn rate as distance increases
    base_speed = 12
    max_speed = 28
    player.forward_speed = min(base_speed + player.z * 0.01, max_speed)
    base_interval = 1.2
    min_interval = 0.35
    spawn_interval = max(base_interval - player.z * 0.0015, min_interval)
    # Smoother player movement with inertia
    input_dir = Vec3(
        (held_keys['d'] - held_keys['a']),
        (held_keys['w'] - held_keys['s']),
        0
    )
    if input_dir.length() > 0:
        input_dir = input_dir.normalized()
    # Interpolate velocity toward input direction
    player.velocity = lerp(player.velocity, input_dir * player.speed, 4 * time.dt)
    player.x += player.velocity.x * time.dt
    player.y += player.velocity.y * time.dt
    player.x = clamp(player.x, -4, 4)
    player.y = clamp(player.y, -3, 3)
    player.z += player.forward_speed * time.dt

    # Camera follows player position, but does not rotate with the ship
    camera.position = (player.x, player.y + 2, player.z - 10)
    camera.rotation = (10, 0, 0)

    # --- Ship rotation logic ---
    # Pitch: up/down (rotation_x), Roll: left/right (rotation_z)
    max_pitch = 5  # degrees (limit)
    max_roll = 5   # degrees (limit)
    # Target pitch: negative when moving up, positive when down
    player.target_rotation_x = clamp(-max_pitch * player.velocity.y / player.speed, -max_pitch, max_pitch)
    # Target roll: negative when moving right, positive when left
    player.target_rotation_z = clamp(-max_roll * player.velocity.x / player.speed, -max_roll, max_roll)
    # Smoothly interpolate current rotation toward target
    player.rotation_x = lerp(player.rotation_x, player.target_rotation_x, 6 * time.dt)
    player.rotation_z = lerp(player.rotation_z, player.target_rotation_z, 6 * time.dt)
    # --- End ship rotation logic ---

    # Power depletes over time
    power -= power_depletion_rate * time.dt
    if power <= 0:
        power = 0
        print('Game Over! (Out of power)')
        game_running = False
        application.paused = True
        show_game_over()
        return
    # Spawn obstacles
    spawn_timer -= time.dt
    if spawn_timer <= 0:
        spawn_obstacle()
        spawn_timer = spawn_interval
    # Spawn energy orbs
    orb_spawn_timer -= time.dt
    if orb_spawn_timer <= 0:
        spawn_energy_orb()
        orb_spawn_timer = orb_spawn_interval
    # Update obstacles and check collision
    obstacles_to_remove = []
    for obstacle in obstacles:
        if obstacle.update():
            obstacles_to_remove.append(obstacle)
            continue
        if check_collision(player, obstacle):
            print('Game Over!')
            game_running = False
            application.paused = True
            show_game_over()
            break
    for obs in obstacles_to_remove:
        obstacles.remove(obs)
    # Handle shooting mode timer
    if shooting_mode:
        shooting_timer -= time.dt
        if shooting_timer <= 0:
            shooting_mode = False
    # Update projectiles
    projectiles_to_remove = []
    for proj in projectiles[:]:
        if not proj.enabled or getattr(proj, '_destroyed', False):
            projectiles.remove(proj)
            continue
        if proj.update():
            if proj in projectiles:
                projectiles.remove(proj)
    # Update orbs and check collection
    orbs_to_remove = []
    for orb in energy_orbs:
        if orb.update():
            orbs_to_remove.append(orb)
            continue
        if check_orb_collision(player, orb):
            if orb.orb_type == 'power':
                power = min(1.0, power + power_orb_value)
            elif orb.orb_type == 'speed_up':
                player.forward_speed += 8
                invoke(setattr, player, 'forward_speed', 12, delay=3)
            elif orb.orb_type == 'slow_down':
                player.forward_speed = max(6, player.forward_speed - 6)
                invoke(setattr, player, 'forward_speed', 12, delay=3)
            elif orb.orb_type == 'shooter':
                shooting_mode = True
                shooting_timer = 10
            orbs_collected += 1
            destroy(orb)
            orbs_to_remove.append(orb)
    for orb in orbs_to_remove:
        energy_orbs.remove(orb)
    # Update UI
    score_text.text = f'Orbs: {orbs_collected}'
    distance_text.text = f'Distance: {int(player.z)}'
    power_bar.scale_x = 0.39 * power
    if power > 0.5:
        power_bar.color = color.green
    elif power > 0.2:
        power_bar.color = color.yellow
    else:
        power_bar.color = color.red

# At the end of the file, show the start menu on launch
show_start_menu()

app.run() 