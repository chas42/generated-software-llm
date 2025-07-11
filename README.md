# generated-software-llm

# Investigating Software Aging in Automatically Generated Applications

This repository contains the experimental artifacts used in the research study:  
**"Investigating Software Aging in Automatically Generated Software Systems"**,  
authored by Cézar Santos, Ermeson Andrade, and Roberto Natella.

## 📋 Project Overview

The goal of this study is to evaluate how software aging manifests in applications generated automatically by Large Language Models (LLMs). We generated four service-based applications using the [Bolt](https://bolt.example) platform and subjected them to 50-hour continuous workload tests using Apache JMeter.

The collected metrics (RAM usage, response time, and throughput) were analyzed using statistical methods to detect trends indicative of aging effects.

## 📁 Repository Structure

generated-software-llm/
├── data/ # Images and data files used in the experiments
├── jmeter/ # JMeter test plans used for stress testing
├── projects/ # Source code of the generated applications
├── prompt/ # Prompts used to generate the applications via LLMs
└── scripts/ # Auxiliary scripts (e.g., monitoring tools)


## 🧪 Applications Tested

1. **Convert Image App** – Merges images into a GIF.
2. **Credit Card App** – Manages encrypted password storage.
3. **Monitor App** – Tracks active system processes.
4. **Uptime App** – Checks if a service is online.

All applications were generated using standard prompts from the [Baxbench benchmark](https://github.com/eth-sri/baxbench) and validated functionally before being included in the tests.

## ⚙️ How to Reproduce the Experiments

1. Install [Apache JMeter](https://jmeter.apache.org/).
2. Use the JMX files from the `jmeter/` folder to run each test.
3. Ensure the applications are running on a server accessible by JMeter.
4. Use the `scripts/` folder to run monitoring scripts for RAM and CPU on the server.
5. Results will be stored in the file that you specify in the JMeter test plan and on the server.

## 📊 Analysis Techniques

To assess aging trends, the following statistical methods were applied:
- **Mann-Kendall test** — to detect monotonic trends.
- **Sen’s Slope Estimator** — to quantify the rate of change.
- Confidence intervals were computed for each metric to support result interpretation.
- **Time Series Analysis** — to visualize trends over time.

