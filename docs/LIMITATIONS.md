# AERIS — Known Limitations

> This document honestly states the limitations of the AERIS prototype.

## General

1. **Synthetic Data Only**: All data is computer-generated. No real aircraft, operational, or defence data is used. Predictions and metrics are based on synthetic degradation patterns and are not validated against real-world failure modes.

2. **Not Airworthy**: This system does not provide airworthiness certifications, release-to-service decisions, or any form of operational aircraft maintenance authorisation.

3. **No Certification Claims**: The system does not claim compliance with any aviation standard (ARP4761, MSG-3, DO-178C, etc.), military standard, or security certification (Common Criteria, NIST, etc.).

## Security

4. **Self-Signed TLS Certificate**: The demo uses a self-signed certificate. Production deployment requires a proper CA-signed certificate.

5. **No HSM**: Cryptographic keys are stored as files (Docker secrets). Production deployment should use a Hardware Security Module (HSM) or key management service.

6. **No Volume Encryption**: Database volume encryption is the responsibility of the deployment environment (e.g., LUKS, BitLocker, cloud-managed encryption).

7. **No Postgres TLS**: Communication between backend and PostgreSQL is unencrypted within the internal Docker network. Production should enable PostgreSQL TLS.

8. **Single-Node Deployment**: The demo runs on a single machine. Production would require HA, load balancing, and proper backup strategies.

## ML / Analytics

9. **Simplified Physics**: Degradation models use statistical patterns (exponential/linear trends with noise), not physics-based simulation. Real failure modes are far more complex.

10. **Limited Failure Modes**: Only 4 failure modes are modelled (2 engine, 2 hydraulic pump). Real aircraft have hundreds of potential failure modes.

11. **No Cross-Component Interactions**: The model does not capture cascading failures or interactions between subsystems.

12. **Gearbox Limitation**: Gearbox components support only anomaly detection and rule-based thresholds. RUL prediction is not supported due to insufficient degradation data. This is honestly displayed in the UI.

13. **Conformal Prediction Calibration**: RUL uncertainty intervals are calibrated on synthetic data. Real-world coverage guarantees would require calibration on operational data.

## Operational

14. **No Real-Time Streaming**: MQTT/IoT streaming is simulated by the "simulate next cycles" action. Real integration would require a message broker (e.g., Kafka, MQTT broker).

15. **Greedy Facility Allocation**: Maintenance slot allocation uses a greedy heuristic. Optimal scheduling would benefit from OR-Tools or similar constraint solver (Phase 2 roadmap).

16. **No Multi-Tenancy**: The system is designed for a single organisation. Multi-tenancy would require additional access controls and data isolation.
