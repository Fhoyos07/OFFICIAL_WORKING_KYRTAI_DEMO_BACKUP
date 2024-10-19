import subprocess

def call_textra():
    # Display the initial prompt for user input.
    input_str = input("GBruno v0.4.1 (Anthony DiPrizio) - Please enter a PDF name followed by a switch (-o) and then an output name such as output.txt: ")

    # Prepare the command to be executed.
    # Assuming 'textra' is the correct command to call the application.
    command = f"textra {input_str}"

    # Call the 'textra' application with the user's input using subprocess.
    try:
        # Run the command and capture the output.
        result = subprocess.run(command, shell=True, check=True, text=True)
        print("GBruno called successfully.")
    except subprocess.CalledProcessError as e:
        # Handle errors in the subprocess
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    call_textra()