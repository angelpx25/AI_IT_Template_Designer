<style>
    /* Reset the default margin and padding for lists */
    ol, ul {
        margin: 0;
        padding: 0;
        display: block;
    }

    p {
        margin: 0; /* Remove default margin for paragraphs */
    }

    p.title {
        color: #FF5733;
        text-align: center;
        font-size: 38px;
        font-weight: bold;
        margin-bottom: 20px;
    }

    p.section-heading {
        color: #333;
        font-size: 24px;
        margin-bottom: 10px;
    }

    a {
        color: #007BFF;
        text-decoration: none;
    }

    a:hover {
        text-decoration: underline;
    }

</style>

<!-- <p class="title">Project Fuel Template Designer Manual</p> -->

<p class="section-heading">Introduction</p>
<p>Welcome to the Project Fuel Template Designer! This tool is designed to help you download templates of workplans
    for Project Fuel clients efficiently. It is developed in Python using Streamlit.</p>
    
<p class="section-heading">Table of Contents</p>
<ol>
    <li><a href="#getting-started">Getting Started</a></li>
    <li><a href="#selecting-proposal-information">Selecting Proposal Information</a></li>
    <li><a href="#client-specific-options">Client-specific Options</a></li>
    <li><a href="#advanced-settings">Advanced Settings</a></li>
    <li><a href="#downloading-the-workplan">Downloading the Workplan</a></li>
</ol>

<p class="section-heading" id="getting-started">1. Getting Started</p>
<p>To begin using the Project Fuel Template Designer, follow these steps:</p>
<ul>
    <li>Open the tool using the provided link or by running the Python script.</li>
    <li>The tool's interface will appear, featuring options for selecting proposal information, client details, and
        more.</li>
</ul>

<p class="section-heading" id="selecting-proposal-information">2. Selecting Proposal Information</p>

<p class="section-heading">2.1 Proposal Name</p>
<ol>
    <li>Start by selecting a proposal name from the available options.</li>
    <li>This step is crucial as it forms the basis for further customization.</li>
</ol>

<p class="section-heading">2.2 Business Requirements</p>
<ol>
    <li>After selecting a proposal name, proceed to input the business requirements.</li>
    <li>These requirements will influence the subsequent steps in the template design process.</li>
</ol>

<p class="section-heading">2.3 Client</p>
<ol>
    <li>Choose the client for whom the workplan is being designed.</li>
    <li>The available client options will determine the specific details that follow.</li>
</ol>

<p class="section-heading">2.4 Proposal Number</p>
<ol>
    <li>Enter the proposal number associated with the selected client.</li>
</ol>

<p class="section-heading" id="client-specific-options">3. Client-specific Options</p>
<p>Upon selecting a client, additional options may appear based on client-specific requirements. These may include:
</p>
<ul>
    <li>Technology options</li>
    <li>Make and model specifications</li>
    <li>Procedure details</li>
</ul>

<p class="section-heading" id="advanced-settings">4. Advanced Settings</p>
<p>To access advanced settings:</p>
<ol>
    <li>Insert a proposal name.</li>
    <li>Additional customization options, such as advanced technology settings, will become available.</li>
</ol>

<p class="section-heading" id="downloading-the-workplan">5. Downloading the Workplan</p>
<p>Once you have completed all necessary selections and inputs:</p>
<ol>
    <li>A "Download" button will appear at the bottom of the sidebar.</li>
    <li>Click on the "Download" button to generate an Excel file containing all the procedures and phases.</li>
    <li>The file will be automatically downloaded to your device.</li>
</ol>
</br>
<p class="section-heading" id="downloading-the-workplan">Version: 0.05</p>
<p>
Latest updates:</br>
-Basic usable version completed.
</br></br>
Next updates:</br>
-Insert multiple procedures in the same proposal.
</p>
