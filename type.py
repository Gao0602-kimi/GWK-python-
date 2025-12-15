"""
Simple Pong (乒乓球) using Pygame.

Controls:
- Mouse move over window: move left paddle
- Arrow Up / Arrow Down: move left paddle
- Space: pause / resume
- R: reset scores and restart
- Esc or close window: quit
"""
import pygame
import sys
import random
import math

# -------------------- 配置 --------------------
WIDTH, HEIGHT = 800, 500
FPS = 60

PADDLE_W = 12
PADDLE_H = 100
PADDLE_OFFSET = 20
PLAYER_SPEED = 7
AI_MAX_SPEED = 5

BALL_RADIUS = 8
BALL_SPEED = 5
BALL_SPEED_INC = 0.5
BALL_MAX_SPEED = 14

FONT_SIZE = 40

# 颜色
BG = (8, 16, 28)
PADDLE_COLOR = (25, 181, 254)
BALL_COLOR = (233, 248, 255)
MIDLINE_COLOR = (255, 255, 255, 30)
TEXT_COLOR = (230, 238, 248)

# -------------------- 类与函数 --------------------
class Paddle:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, PADDLE_W, PADDLE_H)
        self.speed = PLAYER_SPEED

    def move_to(self, y):
        # 使挡板中心对准 y
        self.rect.centery = max(PADDLE_H//2, min(HEIGHT - PADDLE_H//2, int(y)))

    def move_by(self, dy):
        self.rect.y += dy
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > HEIGHT:
            self.rect.bottom = HEIGHT

    def draw(self, surf):
        pygame.draw.rect(surf, PADDLE_COLOR, self.rect, border_radius=4)

class Ball:
    def __init__(self):
        self.reset(None)

    def reset(self, serving_to=None):
        self.x = WIDTH / 2
        self.y = HEIGHT / 2
        self.r = BALL_RADIUS
        self.speed = BALL_SPEED
        # 随机角度 -30 ~ 30 度
        angle = random.uniform(-math.pi/6, math.pi/6)
        # 方向: left (-1) or right (+1)
        if serving_to == 'left':
            dirx = -1
        elif serving_to == 'right':
            dirx = 1
        else:
            dirx = random.choice([-1, 1])
        self.vx = dirx * self.speed * math.cos(angle)
        self.vy = self.speed * math.sin(angle)

    def update(self):
        self.x += self.vx
        self.y += self.vy

    def rect(self):
        return pygame.Rect(int(self.x - self.r), int(self.y - self.r), self.r*2, self.r*2)

    def draw(self, surf):
        pygame.draw.circle(surf, BALL_COLOR, (int(self.x), int(self.y)), self.r)

# 简单的圆与矩形碰撞（用于更精确的球与挡板碰撞）
def circle_rect_collision(cx, cy, r, rect: pygame.Rect):
    closest_x = max(rect.left, min(cx, rect.right))
    closest_y = max(rect.top, min(cy, rect.bottom))
    dx = cx - closest_x
    dy = cy - closest_y
    return dx*dx + dy*dy <= r*r

# 根据击中位置改变反弹角度
def reflect_ball_from_paddle(ball: Ball, paddle: Paddle, is_left_paddle: bool):
    # 计算相对位置 -1..1
    paddle_center = paddle.rect.top + paddle.rect.height / 2
    relative = (ball.y - paddle_center) / (paddle.rect.height / 2)
    relative = max(-1, min(1, relative))
    bounce_angle = relative * (math.pi / 4)  # 最大 45 度
    speed = min(BALL_MAX_SPEED, math.hypot(ball.vx, ball.vy) + BALL_SPEED_INC)
    if is_left_paddle:
        ball.vx = abs(speed * math.cos(bounce_angle))
    else:
        ball.vx = -abs(speed * math.cos(bounce_angle))
    ball.vy = speed * math.sin(bounce_angle)
    ball.speed = speed

# -------------------- 游戏主循环 --------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Pong - 乒乓球 (Pygame)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, FONT_SIZE)

    # 对象
    left_paddle = Paddle(PADDLE_OFFSET, (HEIGHT - PADDLE_H) // 2)
    right_paddle = Paddle(WIDTH - PADDLE_W - PADDLE_OFFSET, (HEIGHT - PADDLE_H) // 2)
    ball = Ball()

    left_score = 0
    right_score = 0

    running = True
    paused = False

    show_cursor = True
    pygame.mouse.set_visible(show_cursor)

    while running:
        dt = clock.tick(FPS) / 1000.0  # seconds elapsed, 未直接用于速度（这里使用像素帧速常量）
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    left_score = 0
                    right_score = 0
                    ball.reset()
                    paused = False
            elif event.type == pygame.MOUSEMOTION:
                # 鼠标移动控制左挡板
                mx, my = event.pos
                left_paddle.move_to(my)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            left_paddle.move_by(-left_paddle.speed)
        if keys[pygame.K_DOWN]:
            left_paddle.move_by(left_paddle.speed)

        if paused:
            # 画暂停界面，但不更新游戏逻辑
            screen.fill(BG)
            draw_midline(screen)
            left_paddle.draw(screen)
            right_paddle.draw(screen)
            ball.draw(screen)
            draw_scores(screen, font, left_score, right_score)
            draw_center_text(screen, font, "PAUSED - Space to resume", y_offset=30)
            pygame.display.flip()
            continue

        # 更新 AI（右挡板）: 跟踪球，限制最大移动速度
        target_y = ball.y
        diff = target_y - (right_paddle.rect.top + right_paddle.rect.height / 2)
        if abs(diff) > 4:
            move = max(-AI_MAX_SPEED, min(AI_MAX_SPEED, diff))
            right_paddle.move_by(move)

        # 更新球
        ball.update()

        # 壁碰撞 (上下)
        if ball.y - ball.r <= 0:
            ball.y = ball.r
            ball.vy = -ball.vy
        elif ball.y + ball.r >= HEIGHT:
            ball.y = HEIGHT - ball.r
            ball.vy = -ball.vy

        # 挡板碰撞
        if circle_rect_collision(ball.x, ball.y, ball.r, left_paddle.rect):
            # 为避免粘连，将球位置移动到挡板外侧
            ball.x = left_paddle.rect.right + ball.r
            reflect_ball_from_paddle(ball, left_paddle, is_left_paddle=True)

        if circle_rect_collision(ball.x, ball.y, ball.r, right_paddle.rect):
            ball.x = right_paddle.rect.left - ball.r
            reflect_ball_from_paddle(ball, right_paddle, is_left_paddle=False)

        # 得分检测
        if ball.x - ball.r <= 0:
            # 右方得分
            right_score += 1
            ball.reset(serving_to='right')
        elif ball.x + ball.r >= WIDTH:
            left_score += 1
            ball.reset(serving_to='left')

        # 渲染
        screen.fill(BG)
        draw_midline(screen)
        left_paddle.draw(screen)
        right_paddle.draw(screen)
        ball.draw(screen)
        draw_scores(screen, font, left_score, right_score)

        # 小提示
        draw_center_text(screen, pygame.font.SysFont(None, 20),
                         "Mouse or Up/Down to move · Space pause · R reset", y_offset=HEIGHT//2 - 10, alpha=180)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

# 画中线
def draw_midline(surface):
    dash_h = 12
    gap = 8
    line_x = WIDTH // 2
    for y in range(0, HEIGHT, dash_h + gap):
        pygame.draw.rect(surface, (255,255,255,30), (line_x - 1, y, 2, dash_h))

# 画分数
def draw_scores(surface, font, left_score, right_score):
    left_surf = font.render(str(left_score), True, TEXT_COLOR)
    right_surf = font.render(str(right_score), True, TEXT_COLOR)
    sep_surf = font.render("—", True, TEXT_COLOR)
    # 居中排列
    total_w = left_surf.get_width() + sep_surf.get_width() + right_surf.get_width() + 40
    x = (WIDTH - total_w) // 2
    surface.blit(left_surf, (x, 20))
    x += left_surf.get_width() + 20
    surface.blit(sep_surf, (x, 20))
    x += sep_surf.get_width() + 20
    surface.blit(right_surf, (x, 20))

# 居中提示文本
def draw_center_text(surface, font, text, y_offset=0, alpha=255):
    surf = font.render(text, True, TEXT_COLOR)
    # 如果需要半透明，就创建带 alpha 的 Surface（这里简单用直接绘制）
    rect = surf.get_rect(center=(WIDTH//2, HEIGHT//2 + y_offset))
    surface.blit(surf, rect)

if __name__ == "__main__":
    main()