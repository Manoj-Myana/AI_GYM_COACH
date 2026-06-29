from services.config.workout_config import PROMPT


class LLMCoach:
    def __init__(self, groq_client):
        self.client = groq_client
        self.history = []
        self.system_prompt = PROMPT

    def give_feedback(self, event, issue):
        # If no external LLM client is configured, fall back to simple
        # template-based feedback so voice coaching still works offline.
        if self.client is None:
            if event == "set_completed":
                return "Nice work — you completed a set. Keep it up!"

            if event == "workout_completed":
                return "Workout complete. Great job today — rest and hydrate!"

            if event == "no_pose_detected":
                return issue or "No pose detected. Please step into the camera frame."

            # Generic feedback when an issue is present
            if issue:
                return issue

            return "Good job — keep going!"

        # Use the configured Groq LLM client when available.
        prompt = f"Event: {event}"

        if issue:
            prompt += f" Form Issue: {issue}"

        messages = [
            {"role": "system", "content": self.system_prompt},
            *self.history[-10:],
            {"role": "user", "content": prompt},
        ]

        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.4,
        )

        text = response.choices[0].message.content.strip()
        self.history.append({"role": "assistant", "content": text})

        return text
