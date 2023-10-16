## PGit: A Comprehensive Tool for Managing Language Model Prompts

**PGit** provides a robust, intuitive system to manage all your large language model (LLM) prompts and their associated settings and metadata in a version-controlled, streamlined fashion. By using a structured YAML schema for prompt storage and an API server for interaction with a Git repository, PGit transforms prompts into reusable pieces of code.

The feature-rich software includes:

**1. Prompt Schema:** Store prompts and their associated metadata using a predefined YAML schema. You can also link prompts to represent chains and create "packs" of prompts that represent specific tasks or workflows. The schema accommodates all types of prompt text or templates, and can store details about the LLM provider, model, and settings.

**2. Command-line Utilities:** PGit provides command-line utilities for creating and viewing prompt files. Additionally, these utilities can present statistics about your prompts, providing insight into their distribution and utilization.

**3. API Server:** The API server lets you upload or retrieve prompts easily. With version control enabled through Git, this feature ensures the integrity and traceability of your prompts.

**4. Validation Tools:** With a validation utility, you can ensure that all prompts adhere to the schema and possess unique UUIDs. In case of duplicate UUIDs, the software provides an option to create new ones automatically.

**5. Statistics Utility:** A dedicated command-line utility provides statistics about your prompts. With this, you can view the distribution of category, provider, and model fields in tabulated format, giving you a clear overview of your prompts.

**6. LangChain Compatibility:** PGit prompts can be effortlessly converted to LangChain Prompt Templates using the provided utility.

**7. Prompt Creation:** A command-line utility lets you create a prompt interactively, adhering to the PGit schema. This feature is currently a proof of concept and is under development for further enhancements.

In the ever-growing world of AI, PGit brings a much-needed order to manage language model prompts efficiently. Its features resonate with the industry's demand for traceability and reusability, making it a quintessential tool for anyone dealing with large language models.


## Technical Overview

**Prompt Validation and Statistics Utility**

This utility is implemented as a Python script that uses the pykwalify library for schema validation and the pandas library for statistics generation. It provides functionalities for prompt validation, statistics generation, and UUID generation. The utility ensures that all prompts adhere to the prompt-serve schema and have unique UUIDs, which is crucial for maintaining the integrity and consistency of the prompts. The statistics generation feature provides insights into the distribution and utilization of the prompts, which can be useful for understanding the composition of the prompt collection and for identifying trends and patterns in the prompts.

## Prompt-Loader

Prompt-Loader is a Python script that uses the requests library to fetch the YAML file containing the prompt from the specified GitHub repository. The YAML file is then parsed using the PyYAML library to extract the prompt data. The script provides options to save the prompt data to a local file or print it to the console in either YAML or JSON format. This script is particularly useful for repositories with a directory structure of /prompts/$category/$promptname.yml.

## Why It's Needed

pgit is needed to manage large collections of prompts in a structured and version-controlled manner. It allows for easy sharing and version control of prompts and enables the association of specific prompts with certain models or settings, such as temperature, penalties, maximum tokens, etc. This is particularly useful when running LLMs locally, as different base models require their prompts in a specific format.
Future Plans

The project plans to add a small API server for uploading/validating new prompts and pushing them to a Git repository. This will further enhance the manageability and reusability of prompts.

## Usage

Both the utility and the script can be run from the command line with various options. For example, to validate all prompts in the prompts/ directory against the schema.yml schema and generate statistics, you can use the following command:

To retrieve a prompt from a GitHub repository and save it to a local file in JSON format, you can use the following command:

```python
python validate.py --schema schema.yml --directory prompts/ --gen-stats
```

To retrieve a prompt from a GitHub repository and save it to a local file in JSON format, you can use the following command:

```python
python prompt_loader.py --repo 'rachittshah/pgit' --prompt 'instruct/summarize' --save 'localfile.json' --json
```