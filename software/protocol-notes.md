# Documentation of the broader Code Integration

## Core Subprograms & Software Components

The architecture is divided into four main functional blocks across the pipeline:

### 1. The Parser
The Parser is responsible for preparing raw data (e.g., text strings, images, or files) for transmission across the constrained serial interface.
* **Functionality:** * Reads the source file or stream into a binary byte array.
  * Slices the binary data into fixed-size, manageable payloads to prevent buffer overflows on the microcontrollers.
  * Formats each chunk into a structured structural packet (Frame Generation).
* **Frame Blueprint:**
  ```
  +--------------+---------------+------------------+---------------+------------+
  | START BYTE   | SEQUENCE NO.  | PAYLOAD LENGTH   | DATA PAYLOAD  | CRC-16     |
  | (e.g., 0x02) | (1-2 Bytes)   | (1 Byte)         | (N Bytes)     | (2 Bytes)  |
  +--------------+---------------+------------------+---------------+------------+
  ```

### 2. The Transmission Protocol
This embedded program ingests raw serial frames from the source computer and converts them into time-precise physical light pulses by simulating a UART-Interface.
* **Functionality:**
  * Listens on the USB hardware serial interface for incoming frames.
  * Implements **On-Off Keying** to achieve the best transfer rate: 

### 3. Receiver & Error Detection
The Receiver continuously samples the optical sensor (Phototransistor/Photodiode via a digital comparator) to reconstruct the digital pulse stream.
* **Functionality:**
  * **Frame Boundary Alignment:** Searches for the unique `START BYTE` pattern.
  * **Error Detection:** Extracts the embedded CRC-16 (Cyclic Redundancy Check) checksum from the incoming frame, calculates its own checksum over the received payload, and compares them. If a mismatch occurs, the packet is instantly flagged as corrupted.

### 4. Data Reassembler
The final processing block handles the ingestion, validation, and reconstruction of the transmitted stream.
* **Functionality:**
  * Reads decoded frames via USB Serial from the Receiver Microcontroller.
  * **Packet Ordering:** Evaluates the `SEQUENCE NO.` field. Since packets can theoretically be lost or dropped due to critical optical alignment failures, it ensures packets are inserted into the memory buffer in the correct index order.
  * **Error Handling & Repair:** Identifies missing packets in the sequence chain and outputs a telemetry error report.
  * Compiles the verified payload buffer back into its original file format (e.g., rewriting a `.png` file).

## Next-Steps:
* implementing Manchester Encoding
* implementing advanced Error-Handling
