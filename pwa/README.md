# Personal AI iPhone PWA

This PWA is a physical-iPhone qualification client for P3. It is not a replacement for the frozen desktop Home V1.

Production requirements:

- serve `server.cloud_app:app` behind HTTPS
- set `PERSONAL_AI_IPHONE_ENROLLMENT_CODE` to a random secret of at least 12 characters
- keep `PERSONAL_AI_IPHONE_ALLOW_INSECURE=false`
- configure the model/provider on the server; provider secrets never belong in browser storage
- use persistent storage for Personal AI data and P3 evidence

Open `/iphone/` on the physical iPhone. Enrollment creates a trusted `ios-pwa` device using the existing device registry and stores the resulting credential in Secure, HttpOnly, SameSite=Strict cookies.

A CI pass proves implementation readiness only. Physical voice qualification requires real iPhone sessions and the frozen P3.1 evidence gates.
