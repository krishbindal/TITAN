import cv2


class Visualizer:

    def draw(self, frame, detections, action=None):
        image = frame.copy()

        for detection in detections:
            x, y = int(detection.x), int(detection.y)
            w, h = int(detection.width), int(detection.height)

            # Color coding
            if detection.name.startswith("ally_"):
                color = (255, 200, 50)  # Cyan for allies (BGR)
            elif detection.name.startswith("enemy_"):
                color = (50, 50, 255)  # Red for enemies
            else:
                color = (50, 255, 50)  # Green for cards

            # Draw sci-fi corners instead of full box
            l = 15
            t = 2
            cv2.line(image, (x, y), (x + l, y), color, t)
            cv2.line(image, (x, y), (x, y + l), color, t)
            cv2.line(image, (x + w, y), (x + w - l, y), color, t)
            cv2.line(image, (x + w, y), (x + w, y + l), color, t)
            cv2.line(image, (x, y + h), (x + l, y + h), color, t)
            cv2.line(image, (x, y + h), (x, y + h - l), color, t)
            cv2.line(image, (x + w, y + h), (x + w - l, y + h), color, t)
            cv2.line(image, (x + w, y + h), (x + w, y + h - l), color, t)

            label = f"{detection.name.replace('enemy_', '').replace('ally_', '')} {detection.confidence:.2f}"

            # Text background for readability
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
            cv2.rectangle(image, (x, y - th - 5), (x + tw, y), color, -1)
            cv2.putText(
                image, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1
            )

        # Draw Target Crosshair if an action is taking place
        if action and action.target_x and action.target_y:
            tx, ty = int(action.target_x), int(action.target_y)
            cv2.circle(image, (tx, ty), 20, (0, 255, 255), 2)
            cv2.line(image, (tx - 30, ty), (tx + 30, ty), (0, 255, 255), 1)
            cv2.line(image, (tx, ty - 30), (tx, ty + 30), (0, 255, 255), 1)
            cv2.putText(
                image,
                "TARGET",
                (tx + 25, ty - 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 255),
                2,
            )

        return image
