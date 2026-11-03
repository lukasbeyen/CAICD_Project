from ngspice_interface import dut_testbench
import os

def main():
    project_path = os.getcwd()
    yaml_path = os.path.join(project_path, 'ngspice_interface', 'files', 'yaml_files', 'TwoStage.yaml')
    parameters = {
        'mp1': 10,
        'wp1': 5.0e-07,
        'lp1': 100.0e-09,
        'mn1': 10,
        'wn1': 5.0e-07,
        'ln1': 100.0e-09,
        'mp3': 10,
        'wp3': 5.0e-07,
        'lp3': 100.0e-09,
        'mn3': 10,
        'wn3': 5.0e-07,
        'ln3': 100.0e-09,
        'mn4': 10,
        'wn4': 5.0e-07,
        'ln4': 100.0e-09,
        'mn5': 10,
        'wn5': 5.0e-07,
        'ln5': 100.0e-09,
        'cap': 5.0e-12,
        'res': 5.0e+3
    }
    process = "TT"
    temp_pvt = 27
    vdd = 1.2
    # Create an instance of the DUT class
    dut = dut_testbench.DUT(yaml_path)
    new_netlist_path = dut.create_new_netlist(parameters, process, temp_pvt, vdd)
    info = dut.simulate(new_netlist_path)
    print(f"New netlist created at: {new_netlist_path}")
    print("info:", info)
    print("trf:", dut.trf)
    print("period:", dut.period)
    print("VDD:", dut.VDD)
    # Measure metrics
    metrics = dut.measure_metrics()

    # Print the measured metrics
    print("Measured Metrics:")
    for key, value in metrics.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()          

