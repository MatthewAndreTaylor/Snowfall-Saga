from collections import deque
from flask import Flask, render_template
from flask_sock import Sock
from simple_websocket import ConnectionClosed
from Box2D import (
    b2World,
    b2Vec2,
    b2EdgeShape,
    b2FixtureDef,
    b2CircleShape,
    b2PolygonShape,
    b2ContactListener,
)
import json
import random
import pygame

app = Flask(__name__)
sock = Sock(app)

WIDTH, HEIGHT = 800, 1000
world = b2World(gravity=(0, 0), doSleep=True)

goal_width = WIDTH / 3 / 10
goal_height = 3

top_goal = world.CreateStaticBody(
    position=(WIDTH / 2 / 10, HEIGHT / 10 - goal_height / 2),
    fixtures=b2FixtureDef(
        shape=b2PolygonShape(box=(goal_width / 2, goal_height / 2)), restitution=1.0
    ),
)

bottom_goal = world.CreateStaticBody(
    position=(WIDTH / 2 / 10, goal_height / 2),
    fixtures=b2FixtureDef(
        shape=b2PolygonShape(box=(goal_width / 2, goal_height / 2)), restitution=1.0
    ),
)

p0_player_bodies = []

p0_player_bodies.append(
    world.CreateDynamicBody(
        position=(WIDTH / 2 / 10, 5),
        shapes=b2CircleShape(radius=3),
        linearDamping=0.6,
        angularDamping=0.5,
    )
)

# p0_player_bodies.append(
#     world.CreateDynamicBody(
#         position=(WIDTH / 4 / 10, 5),
#         shapes=b2CircleShape(radius=2),
#         linearDamping=0.5,
#         angularDamping=0.5
#     )
# )

p1_player_bodies = []

p1_player_bodies.append(
    world.CreateDynamicBody(
        position=(WIDTH / 2 / 10, HEIGHT / 10 - 5),
        shapes=b2CircleShape(radius=3),
        linearDamping=0.6,
        angularDamping=0.5,
    )
)

# p1_player_bodies.append(
#     world.CreateDynamicBody(
#         position=(WIDTH / 4 / 10, 10),
#         shapes=b2CircleShape(radius=2),
#         linearDamping=0.5,
#         angularDamping=0.5
#     )
# )

balls = []
for _ in range(10):
    x = random.randint(100, WIDTH - 100) / 10
    y = random.randint(100, HEIGHT - 100) / 10
    body = world.CreateDynamicBody(
        position=(x, y), linearDamping=0.1, angularDamping=0.4
    )
    shape = body.CreateCircleFixture(radius=2, density=0.02, friction=0.3)
    balls.append((body, shape))

wall_top = world.CreateStaticBody(
    position=(0, HEIGHT / 10),
    fixtures=b2FixtureDef(
        shape=b2EdgeShape(vertices=[(0, 0), (WIDTH / 10, 0)]), restitution=1.0
    ),
)

wall_bottom = world.CreateStaticBody(
    position=(0, 0),
    fixtures=b2FixtureDef(
        shape=b2EdgeShape(vertices=[(0, 0), (WIDTH / 10, 0)]), restitution=1.0
    ),
)

wall_left = world.CreateStaticBody(
    position=(0, 0),
    fixtures=b2FixtureDef(
        shape=b2EdgeShape(vertices=[(0, 0), (0, HEIGHT / 10)]), restitution=1.0
    ),
)

wall_right = world.CreateStaticBody(
    position=(WIDTH / 10, 0),
    fixtures=b2FixtureDef(
        shape=b2EdgeShape(vertices=[(0, 0), (0, HEIGHT / 10)]), restitution=1.0
    ),
)

scores = [0, 0]


class GoalContactListener(b2ContactListener):
    def __init__(self):
        super(GoalContactListener, self).__init__()
        self.bodies_to_remove = []

    def BeginContact(self, contact):
        fixtureA = contact.fixtureA
        fixtureB = contact.fixtureB

        # Check if one of the fixtures is a ball and the other is a goal
        if fixtureA.body in [ball[0] for ball in balls] and fixtureB.body in [
            top_goal,
            bottom_goal,
        ]:
            ball_body = fixtureA.body
            self.bodies_to_remove.append(ball_body)
            if fixtureB.body == bottom_goal:
                scores[1] += 1
            else:
                scores[0] += 1

        elif fixtureB.body in [ball[0] for ball in balls] and fixtureA.body in [
            top_goal,
            bottom_goal,
        ]:
            ball_body = fixtureB.body
            self.bodies_to_remove.append(ball_body)
            if fixtureA.body == bottom_goal:
                scores[1] += 1
            else:
                scores[0] += 1

    def remove_bodies(self):
        for body in self.bodies_to_remove:
            # Instead of removing move the object very far away
            body.position = (100, 100)
        self.bodies_to_remove = []


# Set up the contact listener
contact_listener = GoalContactListener()
world.contactListener = contact_listener

pygame.init()
clock = pygame.time.Clock()


@app.route("/", methods=["GET", "POST"])
def home():
    return render_template("index.html")


@sock.route("/echo")
def echo(connection):
    print("Client connected", connection)

    while True:
        world.Step(1 / 30, 5, 2)
        contact_listener.remove_bodies()
        clock.tick(60)

        try:
            # send the world data to the clients
            player0_data = []

            for i, player_body in enumerate(p0_player_bodies):
                position = (
                    player_body.transform * player_body.fixtures[0].shape.pos * 10
                )
                player0_data.append(
                    {"x": int(position[0]), "y": int(position[1]), "id": i}
                )

            player1_data = []

            for i, player_body in enumerate(p1_player_bodies):
                position = (
                    player_body.transform * player_body.fixtures[0].shape.pos * 10
                )
                player1_data.append(
                    {"x": int(position[0]), "y": int(position[1]), "id": i}
                )

            balls_data = []

            for i, (body, shape) in enumerate(balls):
                position = body.transform * shape.shape.pos * 10
                balls_data.append(
                    {"x": int(position[0]), "y": int(position[1]), "id": i}
                )

            message = {
                "player0": player0_data,
                "balls": balls_data,
                "player1": player1_data,
                "scores": scores,
            }

            if scores[0] >= 5:
                # User 0 wins
                # if current user team is 0, current_user.points increase by 200
                break
            elif scores[1] >= 5:
                # User 1 wins
                # if current user team is 0, current_user.points increase by 200
                break

            connection.send(json.dumps(message))
        except (ConnectionClosed, ConnectionError):
            print("Connection closed")
            break


teams = {}
clients = {}

# TODO map the current user to the team they control


@sock.route("/input")
def input(connection):
    if len(clients) >= 2:
        connection.send(json.dumps({"error": "Game is full"}))
        return

    if teams.get(0) is None:
        teams[0] = connection
        clients[connection] = 0
        print(teams)
    else:
        teams[1] = connection
        clients[connection] = 1
        print(teams)

    while True:
        try:
            message = connection.receive()
            data = json.loads(message)

            if clients[connection] == 0:
                p0_player_bodies[0].ApplyLinearImpulse(
                    b2Vec2(data["x"], data["y"]), p0_player_bodies[0].worldCenter, True
                )
            else:
                p1_player_bodies[0].ApplyLinearImpulse(
                    b2Vec2(data["x"], data["y"]), p1_player_bodies[0].worldCenter, True
                )
        except Exception as e:
            print(e)
            team = clients[connection]
            teams.pop(team)
            clients.pop(connection)
            break
