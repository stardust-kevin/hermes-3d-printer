import asyncio
import cv2
import json
import websockets
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate
from aiortc.sdp import candidate_from_sdp

async def receive_camera_stream():
    print("Connecting to signaling server...")
    uri = "ws://192.168.2.2:3001/camera-signal"

    # Create the WebRTC peer connection
    pc = RTCPeerConnection()

    @pc.on("track")
    def on_track(track):
        print(f"Track received: {track.kind}")
        if track.kind == "video":
            asyncio.ensure_future(display_video(track))

    async def display_video(track):
        print("Displaying camera feed. Press 'q' to quit (if GUI is available).")
        frame_count = 0

        while True:
            try:
                # Receive a video frame
                frame = await track.recv()
                # Convert to numpy array (BGR format for OpenCV)
                img = frame.to_ndarray(format="bgr24")

                # If it's the first frame, save a local snapshot for verification
                if frame_count == 0:
                    cv2.imwrite("snapshot.jpg", img)
                    print(f"\n[SUCCESS] Received first frame! Resolution: {img.shape[1]}x{img.shape[0]}")
                    print(f"[SUCCESS] Saved to local file: snapshot.jpg (You can download and view it).")
                    print("If running on a desktop machine, a window should have popped up.")

                frame_count += 1

                # Try to display the frame in a window
                try:
                    cv2.imshow("3D Printer Virtual Camera", img)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                except cv2.error:
                    # Ignore if running on a headless server (no display)
                    pass

            except Exception as e:
                print(f"Stream ended or error: {e}")
                break
        cv2.destroyAllWindows()

    try:
        # Connect to WebSocket server (proxy=None prevents timeout issues behind proxies)
        async with websockets.connect(uri, proxy=None) as ws:
            print("Signaling server connected. Requesting WebRTC Offer...")

            # Request the frontend to send a new Offer
            await ws.send(json.dumps({"type": "request_offer"}))

            while True:
                # Wait for messages from the browser
                msg_str = await ws.recv()
                msg = json.loads(msg_str)

                if msg["type"] == "offer":
                    print("Received WebRTC Offer, generating Answer...")
                    offer = RTCSessionDescription(sdp=msg["sdp"], type=msg["type"])
                    await pc.setRemoteDescription(offer)

                    # Create and send Answer
                    answer = await pc.createAnswer()
                    await pc.setLocalDescription(answer)

                    await ws.send(json.dumps({
                        "type": "answer",
                        "sdp": pc.localDescription.sdp
                    }))

                elif msg["type"] == "ice":
                    # aiortc requires an RTCIceCandidate object, not a raw dictionary
                    cand_data = msg.get("candidate")
                    if cand_data:
                        try:
                            # Extract the raw SDP string
                            sdp_str = cand_data.get("candidate", "")

                            # Parse the SDP string into an aiortc object
                            ice = candidate_from_sdp(sdp_str)

                            # Attach the other required fields
                            ice.sdpMid = cand_data.get("sdpMid", "0")
                            ice.sdpMLineIndex = cand_data.get("sdpMLineIndex", 0)

                            await pc.addIceCandidate(ice)
                        except Exception as e:
                            print(f"Failed to add ICE candidate: {e}")

    except websockets.exceptions.ConnectionClosed:
        print("Signaling connection closed.")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        print("Closing WebRTC connection...")
        await pc.close()

if __name__ == "__main__":
    try:
        asyncio.run(receive_camera_stream())
    except KeyboardInterrupt:
        print("Stopped by user.")