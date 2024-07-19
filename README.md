# FileSwoosh

This is the documentation for the project software engineering course at the IU.
Find the following in the subfolders:

- [docs](./docs/) some diagrams and video footage of the app in action
- [iu](./iu/) the PDF documents as required by course adssignment
- [source](./source/) the pure source of the app

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

What things you need to install the software and how to install them:

- Python 3.x
- pip (Python package installer)

### Installing

A step by step series of examples that tell you how to get a development environment running:

1. Clone the repository to your local machine:
   ```shell
   git clone https://github.com/hw-iu/FileSwoosh.git
   ```
2. Navigate to the project directory:
   ```shell
   cd FileSwoosh/source
   ```
3. Install the required packages:
   ```shell
   pip install -r requirements.txt
   ```

## Running the Application

To run the application, execute the following command in the project's root directory:

```shell
python main.py
```

For building the application into a standalone executable, use PyInstaller with the following command:

```shell
pyinstaller --onefile --add-data resources/:resources/ --windowed --icon resources/images/logo.ico --name FileSwoosh main.py
```

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](source/LICENSE) file for details.

