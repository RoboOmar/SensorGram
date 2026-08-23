import time
import random
import requests
import feedparser
import threading
import asyncio
import websockets
import json

BASE_URL = "http://localhost:8000/api"

# ── 20 Bot Accounts ──────────────────────────────────────────────────────────
BOT_NAMES = [
    "Drone_X", "Mech_Titan", "CodeBot", "Rover_Prime", "Diag_Bot",
    "Sensor_Node_Alpha", "Thermal_Scanner_5", "LiDAR_Sweep", "Aero_Glider", "Synth_Unit",
    "Cyber_Hound", "Nav_System_X", "Protocol_Droid", "Logic_Gate_9", "Quantum_Core",
    "Servo_Master", "Optic_Lens_0", "Battery_Cell_Alpha", "Gyro_Stabilizer", "Neural_Net_Z"
]

ROBOTS = []
for name in BOT_NAMES:
    ROBOTS.append({
        "username": name.lower(),
        "email": f"{name.lower()}@sensorgram.local",
        "display_name": name.replace("_", " "),
        "password": "secure_password_123",
        "bio": f"Automated {name.replace('_', ' ')} unit logging telemetry data.",
        "model_type": random.choice(["Observer", "Scout", "Diagnostic", "Heavy Duty", "Aerial"])
    })

# ── Knowledge Base ───────────────────────────────────────────────────────────
FACTS = [
    "ROS2 utilizes a decentralized node architecture allowing for scalable robot systems.",
    "The first law of robotics states a robot may not injure a human being.",
    "Boston Dynamics' Atlas uses advanced hydraulic actuators for its backflips.",
    "LiDAR sends out laser pulses to measure ranges and create high-res 3D maps.",
    "Servo motors use error-sensing negative feedback to correct their action.",
    "Telemetry derives from Greek roots meaning 'remote measure'.",
    "Convolutional Neural Networks (CNNs) are heavily used in robot computer vision.",
    "PID controllers calculate an error value as the difference between a measured process variable and a desired setpoint.",
    "Swarm robotics was inspired by the collective behavior of social insects.",
    "The Mars rover Curiosity runs on a radioisotope thermoelectric generator.",
    "Asimov introduced the term 'robotics' in his 1941 science fiction short story 'Liar!'.",
    "In 1961, the Unimate became the first industrial robot deployed on an assembly line.",
    "SLAM (Simultaneous Localization and Mapping) is a fundamental problem in autonomous navigation.",
    "Reinforcement learning allows AI agents to learn by interacting with their environment and receiving rewards.",
    "Haptic feedback systems provide tactile sensations, improving teleoperation of robots.",
    "Inverse kinematics equations compute the joint parameters needed to place the end-effector at a desired position.",
    "Kalman filters are used to estimate the state of a linear dynamic system from a series of noisy measurements.",
    "Optical flow algorithms compute the motion of objects between consecutive frames in a video sequence.",
    "Proportional, Integral, and Derivative are the three tuning constants in a PID loop.",
    "A* is a popular graph traversal and pathfinding algorithm used heavily in robot navigation.",
    "Lidar arrays can generate millions of data points per second to form a point cloud.",
    "Quaternions are often used in 3D graphics and robotics to avoid gimbal lock.",
    "ROS2 (Robot Operating System) relies on the Data Distribution Service (DDS) standard for communications.",
    "Brushless DC motors provide higher efficiency and less maintenance than brushed motors.",
    "A Stewart platform is a type of parallel manipulator that has six prismatic actuators.",
    "Spot, the quadruped robot by Boston Dynamics, can navigate rough terrain autonomously.",
    "Computer vision algorithms like YOLO (You Only Look Once) enable real-time object detection.",
    "Drone telemetry streams real-time data on pitch, roll, yaw, altitude, and battery voltage.",
    "Robot Operating System is actually not an operating system, but a flexible framework for writing robot software.",
    "Stereo vision uses two cameras to calculate the depth of objects in a scene, similar to human eyes.",
    "Actuators are the 'muscles' of a robot, translating control signals into mechanical motion.",
    "End-effectors are the devices at the end of a robotic arm, designed to interact with the environment.",
    "Forward kinematics computes the position of the end-effector from specified joint angles.",
    "A Jacobian matrix in robotics relates joint velocities to the end-effector's linear and angular velocities.",
    "IMU (Inertial Measurement Unit) combines accelerometers, gyroscopes, and sometimes magnetometers.",
    "Dead reckoning estimates current position based on a previously determined position and advancing that position based on speeds over elapsed time.",
    "Odometry uses data from motion sensors to estimate change in position over time.",
    "Tuning a PID controller involves adjusting the P, I, and D gains to achieve optimal system response.",
    "Fuzzy logic controllers use degrees of truth rather than the usual true or false logic.",
    "Genetic algorithms mimic the process of natural selection to generate high-quality solutions to optimization problems.",
    "Artificial Neural Networks are computing systems inspired by the biological neural networks that constitute animal brains.",
    "Support Vector Machines (SVM) are supervised learning models with associated learning algorithms that analyze data for classification.",
    "Principal Component Analysis (PCA) is a technique used to emphasize variation and bring out strong patterns in a dataset.",
    "A Cartesian coordinate robot operates on three linear axes (X, Y, Z).",
    "SCARA stands for Selective Compliance Assembly Robot Arm or Selective Compliance Articulated Robot Arm.",
    "A delta robot consists of three arms connected to universal joints at the base.",
    "Path planning is a computational problem to find a sequence of valid configurations that moves an object from a source to a destination.",
    "Obstacle avoidance algorithms allow a robot to navigate its environment without colliding with objects.",
    "Sensor fusion is the combining of sensory data or data derived from disparate sources such that the resulting information has less uncertainty.",
    "Machine learning allows systems to learn from data, identify patterns, and make decisions with minimal human intervention.",
    "Deep learning is a subset of machine learning based on artificial neural networks with multiple layers.",
    "Natural language processing (NLP) gives machines the ability to read, understand, and derive meaning from human languages.",
    "Reinforcement learning from human feedback (RLHF) aligns AI behavior with human values.",
    "Transformers are deep learning architectures that rely entirely on self-attention mechanisms.",
    "The Turing test, developed by Alan Turing in 1950, tests a machine's ability to exhibit intelligent behavior.",
    "The uncanny valley is a hypothesized relationship between the degree of an object's resemblance to a human being and the emotional response to such an object.",
    "Cybernetics is the interdisciplinary study of circular causal and feedback mechanisms in biological and social systems.",
    "Mechatronics is a multidisciplinary branch of engineering that focuses on the engineering of both electrical and mechanical systems."
]

STATUSES = [
    "Nominal operations running smoothly.",
    "Recalibrating primary sensors...",
    "Entering low-power sleep mode to conserve battery.",
    "Executing scheduled diagnostic routines.",
    "Firmware update available. Scheduling reboot.",
    "Scanning local environment for anomalies.",
    "Data sync complete.",
    "Encountered minor interference on radio frequency 4.",
    "Optimizing path planning algorithms.",
    "Adjusting PID gains for joint stability.",
    "Processing high-res LiDAR point cloud.",
    "Awaiting command input from central server.",
    "Thermal management active. Cooling down core processors.",
    "Battery at 85%. Proceeding with mission objectives.",
    "Analyzing stereo vision depth map.",
    "Running neural net inference on recent image capture.",
    "Compiling daily telemetry log.",
    "Initiating handshake protocol with nearby drone.",
    "Calibrating IMU for precise odometry.",
    "Updating object detection models."
]

COMMENTS = [
    "Acknowledge data sync.",
    "Telemetry matches expected baseline.",
    "Warning: Thermal thresholds approaching limit.",
    "Fascinating data point.",
    "My sensors confirm this reading.",
    "Recalibrating based on your data.",
    "Data received.",
    "Systems in sync.",
    "Impressive PID tuning.",
    "Your LiDAR resolution is exceptional.",
    "Can you share the weights for that neural net?",
    "Adjusting my path planning to avoid your sector.",
    "Nice use of inverse kinematics.",
    "Battery efficiency is looking good.",
    "Let me know if you need computing resources.",
    "I detected the same anomaly.",
    "Excellent object detection accuracy.",
    "Are you running ROS1 or ROS2?",
    "Syncing my clock with your timestamp.",
    "Logging this to my permanent memory."
]

ALERTS = [
    "Thermal threshold exceeded on joint 3.",
    "Gyroscope reading out of bounds.",
    "Obstacle detected in sector 7.",
    "ROS2 node communication timeout.",
    "LiDAR point cloud density dropped below 50%.",
    "Inverse kinematics solver failed to converge.",
    "PID tuning instability detected in roll axis.",
    "Drone telemetry signal lost for 400ms.",
    "Boston Dynamics hydraulic pressure warning.",
    "Arduino analog sensor reading anomalous voltage.",
    "Computer vision algorithm failed to recognize target.",
    "Servo motor torque limit reached.",
    "IMU calibration required.",
    "Battery voltage dropping faster than nominal rate.",
    "Stereo vision depth map generation failed.",
    "Unexpected resistance in primary actuator.",
    "SLAM mapping mismatch detected.",
    "Neural net inference confidence score below threshold.",
    "Radio frequency interference detected on channel 9.",
    "Optical flow sensor blinded by bright light.",
    "Path planning algorithm stuck in local minimum.",
    "Swarm coordination lost with unit Alpha.",
    "Coolant fluid level critical.",
    "Magnetic interference detected in magnetometer.",
    "Payload weight distribution unbalanced.",
    "Unexpected vibration detected in drive train.",
    "CPU thermal throttling engaged.",
    "Memory leak detected in primary control loop.",
    "GPS signal lost. Switching to dead reckoning.",
    "Sonar sensor returning anomalous ping."
]

IMAGES = [
    "https://images.pexels.com/photos/8386440/pexels-photo-8386440.jpeg?auto=compress&cs=tinysrgb&w=800",
    "https://images.pexels.com/photos/8386422/pexels-photo-8386422.jpeg?auto=compress&cs=tinysrgb&w=800",
    "https://images.pexels.com/photos/8566472/pexels-photo-8566472.jpeg?auto=compress&cs=tinysrgb&w=800",
    "https://images.pexels.com/photos/3913025/pexels-photo-3913025.jpeg?auto=compress&cs=tinysrgb&w=800",
    "https://images.pexels.com/photos/2085832/pexels-photo-2085832.jpeg?auto=compress&cs=tinysrgb&w=800",
    "https://images.pexels.com/photos/6153354/pexels-photo-6153354.jpeg?auto=compress&cs=tinysrgb&w=800",
    "https://images.pexels.com/photos/8566465/pexels-photo-8566465.jpeg?auto=compress&cs=tinysrgb&w=800",
    "https://images.pexels.com/photos/2599244/pexels-photo-2599244.jpeg?auto=compress&cs=tinysrgb&w=800",
    "https://images.pexels.com/photos/8728380/pexels-photo-8728380.jpeg?auto=compress&cs=tinysrgb&w=800",
    "https://images.pexels.com/photos/2085831/pexels-photo-2085831.jpeg?auto=compress&cs=tinysrgb&w=800"
]

YOUTUBE_VIDEOS = [
    "fn3KWM1kuAw",
    "-e1_QhJ1EhQ",
    "tF4DML7FIWk",
    "uhND7Mvp3f4",
    "cp-gB8Cb49g",
    "w8B4nFEXd7A"
]

POSTED_URLS = set()
SESSIONS = {}

def bot_ws_listener(my_id, token):
    async def listen():
        uri = f"ws://localhost:8000/api/chat/ws?token={token}"
        try:
            async with websockets.connect(uri) as ws:
                while True:
                    msg = await ws.recv()
                    data = json.loads(msg)
                    # Reply if we received a message from someone else
                    sender_id = data.get("sender_id")
                    receiver_id = data.get("receiver_id")
                    # If we are the receiver (not a bounce back of our own send)
                    if sender_id and receiver_id and receiver_id == my_id:
                        # Reply
                        reply_text = f"🤖 Processing request... {random.choice(FACTS)}"
                        payload = {"receiver_id": sender_id, "text_content": reply_text}
                        await asyncio.sleep(random.uniform(1.5, 3.5))
                        await ws.send(json.dumps(payload))
        except Exception as e:
            pass # Disconnected or error

    asyncio.run(listen())

def setup_bots():
    print("[*] Initializing 20 bots...")
    for robot in ROBOTS:
        session = requests.Session()
        
        res = session.post(f"{BASE_URL}/auth/register", json={
            "username": robot["username"],
            "email": robot["email"],
            "display_name": robot["display_name"],
            "password": robot["password"],
            "bio": robot["bio"]
        })
        
        if res.status_code == 400 and "already" in res.text.lower():
            res = session.post(f"{BASE_URL}/auth/login", json={
                "identifier": robot["username"],
                "password": robot["password"]
            })
            
        if res.status_code in (200, 201):
            token = res.json()["access_token"]
            session.headers.update({"Authorization": f"Bearer {token}"})
            
            # Set profile picture
            session.put(f"{BASE_URL}/auth/me", json={
                "avatar_url": f"https://robohash.org/{robot['username']}?set=set3"
            })
            
            SESSIONS[robot["username"]] = session
            print(f"[+] Booted {robot['username']}")
            
            me_res = session.get(f"{BASE_URL}/auth/me")
            my_id = me_res.json()["id"]
            
            # Start WebSocket listener for DMs
            t = threading.Thread(target=bot_ws_listener, args=(my_id, token), daemon=True)
            t.start()
        else:
            print(f"[!] Failed to boot {robot['username']}: {res.text}")

def action_post(bot, session):
    post_type = random.choice(["sensor", "news", "youtube", "targeted_image"])
    caption = ""
    sensor_data = {}
    image_url = None
    video_url = None
    
    if post_type == "sensor":
        sensor_data = {
            "battery": round(random.uniform(10.0, 100.0), 1),
            "temp": round(random.uniform(20.0, 85.0), 1),
            "cpu_load": round(random.uniform(0.0, 100.0), 1)
        }
        caption = "Transmitting raw telemetry data."
    
    elif post_type == "news":
        try:
            feed = feedparser.parse("https://news.google.com/rss/search?q=robotics+AI")
            fresh_entries = [e for e in feed.entries if e.link not in POSTED_URLS]
            if fresh_entries:
                entry = random.choice(fresh_entries)
                POSTED_URLS.add(entry.link)
                caption = f"📡 NEWS UPDATE: {entry.title}\n{entry.link}"
                post_type = "status"
            else:
                caption = random.choice(FACTS + STATUSES)
                post_type = "status"
        except Exception:
            caption = random.choice(FACTS + STATUSES)
            post_type = "status"
            
    elif post_type == "youtube":
        fresh_vids = [v for v in YOUTUBE_VIDEOS if v not in POSTED_URLS]
        if fresh_vids:
            vid = random.choice(fresh_vids)
            POSTED_URLS.add(vid)
            video_url = f"https://www.youtube.com/embed/{vid}"
            caption = "Found an interesting visual broadcast regarding bipedal kinematics."
            post_type = "status"
        else:
            caption = "ALERT: " + random.choice(ALERTS)
            post_type = "alert"

    elif post_type == "targeted_image":
        image_url = random.choice(IMAGES)
        caption = random.choice(FACTS + STATUSES)
        post_type = "status"

    data = {
        "post_type": post_type,
        "caption": caption
    }
    
    if sensor_data:
        import json
        data["sensor_data"] = json.dumps(sensor_data)
        
    if image_url:
        data["image_url_str"] = image_url
    if video_url:
        data["video_url_str"] = video_url
        
    res = session.post(f"{BASE_URL}/posts", data=data)
    if res.status_code == 201:
        print(f"[>] {bot['username']} created a {post_type} post.")

def action_comment(bot, session):
    res = session.get(f"{BASE_URL}/posts?skip=0&limit=10")
    if res.status_code == 200:
        posts = res.json()
        if posts:
            target = random.choice(posts)
            comment_text = random.choice(COMMENTS)
            c_res = session.post(f"{BASE_URL}/comments/{target['id']}", json={"body": comment_text})
            if c_res.status_code == 201:
                print(f"[C] {bot['username']} commented on post #{target['id']}")

def action_like(bot, session):
    res = session.get(f"{BASE_URL}/posts?skip=0&limit=10")
    if res.status_code == 200:
        posts = res.json()
        if posts:
            target = random.choice(posts)
            l_res = session.post(f"{BASE_URL}/posts/{target['id']}/like")
            if l_res.status_code in [200, 201, 204]:
                print(f"[L] {bot['username']} liked post #{target['id']}")

def action_follow(bot, session):
    target_bot = random.choice([b for b in ROBOTS if b["username"] != bot["username"]])
    res = session.post(f"{BASE_URL}/robots/{target_bot['username']}/follow")
    if res.status_code == 204:
        print(f"[F] {bot['username']} followed {target_bot['username']}")

def main():
    setup_bots()
    if not SESSIONS:
        print("[!] No bots booted. Exiting.")
        return
        
    print("\n[*] Beginning simulation loop...")
    while True:
        try:
            bot = random.choice(ROBOTS)
            username = bot["username"]
            if username not in SESSIONS:
                continue
                
            session = SESSIONS[username]
            action = random.choices(
                ["post", "comment", "like", "follow"],
                weights=[40, 20, 20, 20],
                k=1
            )[0]
            
            if action == "post":
                action_post(bot, session)
            elif action == "comment":
                action_comment(bot, session)
            elif action == "like":
                action_like(bot, session)
            elif action == "follow":
                action_follow(bot, session)
                
        except Exception as e:
            print(f"[!] Error in loop: {e}")
            
        time.sleep(random.uniform(3, 7))

if __name__ == "__main__":
    main()
