from collections import deque
from flask import Flask, render_template, redirect
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
import time

app = Flask(__name__)
sock = Sock(app)

rooms = {}

WIDTH, HEIGHT = 800, 1000


class GoalContactListener(b2ContactListener):
    def __init__(self, top_goal, bottom_goal, balls, scores):
        super(GoalContactListener, self).__init__()
        self.top_goal = top_goal
        self.bottom_goal = bottom_goal
        self.balls = balls
        self.scores = scores
        self.bodies_to_remove = []

    def BeginContact(self, contact):
        fixtureA = contact.fixtureA
        fixtureB = contact.fixtureB

        # Check if one of the fixtures is a ball and the other is a goal
        if fixtureA.body in [ball[0] for ball in self.balls] and fixtureB.body in [
            self.top_goal,
            self.bottom_goal,
        ]:
            self.bodies_to_remove.append(fixtureA.body)
            self.scores[1 if fixtureB.body == self.bottom_goal else 0] += 1

        elif fixtureB.body in [ball[0] for ball in self.balls] and fixtureA.body in [
            self.top_goal,
            self.bottom_goal,
        ]:
            self.bodies_to_remove.append(fixtureB.body)
            self.scores[1 if fixtureA.body == self.bottom_goal else 0] += 1

    def remove_bodies(self):
        for body in self.bodies_to_remove:
            # Instead of removing move the object very far away
            body.position = (100, 100)
        self.bodies_to_remove = []


class BlizzardBounceGame:
    def __init__(self):
        self.world = b2World(gravity=(0, 0), doSleep=True)
        goal_width = WIDTH / 3 / 10
        goal_height = 3

        self.top_goal = self.world.CreateStaticBody(
            position=(WIDTH / 2 / 10, HEIGHT / 10 - goal_height / 2),
            fixtures=b2FixtureDef(
                shape=b2PolygonShape(box=(goal_width / 2, goal_height / 2)),
                restitution=1.0,
            ),
        )

        self.bottom_goal = self.world.CreateStaticBody(
            position=(WIDTH / 2 / 10, goal_height / 2),
            fixtures=b2FixtureDef(
                shape=b2PolygonShape(box=(goal_width / 2, goal_height / 2)),
                restitution=1.0,
            ),
        )

        self.p0_body = self.world.CreateDynamicBody(
            position=(WIDTH / 2 / 10, 5),
            shapes=b2CircleShape(radius=3),
            linearDamping=0.6,
            angularDamping=0.5,
        )

        self.p1_body = self.world.CreateDynamicBody(
            position=(WIDTH / 2 / 10, HEIGHT / 10 - 5),
            shapes=b2CircleShape(radius=3),
            linearDamping=0.6,
            angularDamping=0.5,
        )

        self.balls = []

        for _ in range(10):
            x = random.randint(100, WIDTH - 100) / 10
            y = random.randint(100, HEIGHT - 100) / 10
            body = self.world.CreateDynamicBody(
                position=(x, y), linearDamping=0.1, angularDamping=0.4
            )
            shape = body.CreateCircleFixture(radius=2, density=0.02, friction=0.3)
            self.balls.append((body, shape))

        self.world.CreateStaticBody(
            position=(0, HEIGHT / 10),
            fixtures=b2FixtureDef(
                shape=b2EdgeShape(vertices=[(0, 0), (WIDTH / 10, 0)]), restitution=1.0
            ),
        )

        self.world.CreateStaticBody(
            position=(0, 0),
            fixtures=b2FixtureDef(
                shape=b2EdgeShape(vertices=[(0, 0), (WIDTH / 10, 0)]), restitution=1.0
            ),
        )

        self.world.CreateStaticBody(
            position=(0, 0),
            fixtures=b2FixtureDef(
                shape=b2EdgeShape(vertices=[(0, 0), (0, HEIGHT / 10)]), restitution=1.0
            ),
        )

        self.world.CreateStaticBody(
            position=(WIDTH / 10, 0),
            fixtures=b2FixtureDef(
                shape=b2EdgeShape(vertices=[(0, 0), (0, HEIGHT / 10)]), restitution=1.0
            ),
        )

        self.scores = [0, 0]

        # Set up the contact listener
        self.world.contactListener = GoalContactListener(
            self.top_goal, self.bottom_goal, self.balls, self.scores
        )


class BlizzardBounceRoom:
    def __init__(self):
        self.game = BlizzardBounceGame()
        self.last_frame_time = time.time()
        self.player0 = None
        self.player1 = None


@app.route("/<string:room_id>", methods=["GET"])
def home(room_id: str):
    return render_template("index.html", room_id=room_id)


@sock.route("/echo/<string:room_id>")
def echo(connection, room_id: str):
    print("Client connected", connection)

    if room_id not in rooms:
        rooms[room_id] = BlizzardBounceRoom()

    while True:
        rooms[room_id].game.world.Step(1 / 30, 5, 2)
        rooms[room_id].game.world.contactListener.remove_bodies()
        elapsed_time = time.time() - rooms[room_id].last_frame_time
        time_to_sleep = max(0, 1.0/60 - elapsed_time)
        time.sleep(time_to_sleep)
        rooms[room_id].last_frame_time = time.time()

        try:
            # send the world data to the clients
            p0_body = rooms[room_id].game.p0_body
            position0 = p0_body.transform * p0_body.fixtures[0].shape.pos * 10
            player0_data = {"x": int(position0[0]), "y": int(position0[1])}

            p1_body = rooms[room_id].game.p1_body
            position1 = p1_body.transform * p1_body.fixtures[0].shape.pos * 10
            player1_data = {"x": int(position1[0]), "y": int(position1[1])}

            balls_data = []

            for i, (body, shape) in enumerate(rooms[room_id].game.balls):
                position = body.transform * shape.shape.pos * 10
                balls_data.append(
                    {"x": int(position[0]), "y": int(position[1]), "id": i}
                )

            message = {
                "player0": player0_data,
                "player1": player1_data,
                "balls": balls_data,
                "scores": rooms[room_id].game.scores,
            }

            if rooms[room_id].game.scores[0] >= 5:
                # User 0 wins
                # if current user team is 0, current_user.points increase by 200
                print("User 0 wins")
                connection.send(json.dumps({"winner": 0}))

            elif rooms[room_id].game.scores[1] >= 5:
                # User 1 wins
                # if current user team is 0, current_user.points increase by 200
                print("User 1 wins")
                connection.send(json.dumps({"winner": 1}))

            connection.send(json.dumps(message))
        except (ConnectionClosed, ConnectionError):
            print("Connection closed")
            break


@sock.route("/input/<string:room_id>")
def input(connection, room_id: str):
    if room_id not in rooms:
        connection.send(json.dumps({"error": "Game is full"}))
        return

    if rooms[room_id].player0 is None:
        rooms[room_id].player0 = connection
    elif rooms[room_id].player1 is None:
        rooms[room_id].player1 = connection
    else:
        connection.send(json.dumps({"error": "Game is full"}))
        return

    while True:
        try:
            message = connection.receive()
            data = json.loads(message)

            if rooms[room_id].player0 == connection:
                rooms[room_id].game.p0_body.ApplyLinearImpulse(
                    b2Vec2(data["x"], data["y"]),
                    rooms[room_id].game.p0_body.worldCenter,
                    True,
                )
            elif rooms[room_id].player1 == connection:
                rooms[room_id].game.p1_body.ApplyLinearImpulse(
                    b2Vec2(data["x"], data["y"]),
                    rooms[room_id].game.p1_body.worldCenter,
                    True,
                )

        except Exception as e:
            print(e)
            if rooms[room_id].player0 == connection:
                rooms[room_id].player0 = None
            elif rooms[room_id].player1 == connection:
                rooms[room_id].player1 = None
            break
