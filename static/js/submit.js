document.getElementById('sendData').addEventListener('click', function() {
    const userInput = document.getElementById('userInput').value; // Get the user input value

    const button = document.getElementById('sendData');

    // Define the data to be sent in the request body
    const data = { input: userInput };

    // Check if button is greyed out
    if (button.classList.contains('bg-green-500')) {

        // Set the button text to 'Loading...' when clicked and turn it grey in tailwind css
        button.textContent = 'Loading...';
        button.classList.remove('bg-green-500');
        button.classList.remove('hover:bg-green-600');
        button.classList.add('bg-gray-300');
        
        // Use fetch to send a POST request to the /submit endpoint
        fetch('/submit', {
            method: 'POST', // Specify the request method
            headers: {
                'Content-Type': 'application/json', // Specify the content type of the request body
            },
            body: JSON.stringify(data), // Convert the JavaScript object to a JSON string
        })
        .then(response => response.json()) // Parse the JSON response body
        .then(data => {
            console.log('Submit Success:', data); // Log success message and response data to the console
            const taskId = data.task_id; // Extract task_id from the response
            checkLLMStatus(taskId); // Call function to periodically check task status
            checkRAGStatus(taskId); // Call function to periodically check task status
        })
        .catch((error) => {
            console.error('Submit Error:', error); // Log any errors to the console
        });
    }
});


function checkLLMStatus(taskId) {
    const statusInterval = setInterval(() => {
        fetch(`/status/llm/${taskId}`) // Use template literals to include taskId in the URL
        .then(response => response.json())
        .then(data => {
            console.log('Checking status:', data); // Log the status check
            if (data.status === 'COMPLETE') { // Check if the task status is 'completed'
                clearInterval(statusInterval); // Stop the interval checks
                console.log('LLM Completed:', data); // Log task completion and any data
                
                // Update the paragraph with id="defaultLLMOutput" with the content from data.result
                document.getElementById('defaultLLMOutput').textContent = data.result;
                document.getElementById('llmElectrictiy').textContent = "Stromverbrauch: " + data.electricity + " mWh";

                // Here, you can also update other parts of the UI to reflect the task completion
            }
        })
        .catch((error) => {
            console.error('Status Check Error:', error); // Log any errors to the console
            clearInterval(statusInterval); // Ensure interval is cleared on error to prevent infinite loop
        });
    }, 2000); // Check every 2000 milliseconds (2 seconds)
}

function checkRAGStatus(taskId) {
    const statusInterval = setInterval(() => {
        fetch(`/status/rag/${taskId}`) // Use template literals to include taskId in the URL
        .then(response => response.json())
        .then(data => {
            console.log('Checking status:', data); // Log the status check
            if (data.status === 'COMPLETE') { // Check if the task status is 'completed'
                clearInterval(statusInterval); // Stop the interval checks
                console.log('RAG Completed:', data); // Log task completion and any data
                
                // Update the paragraph with id="defaultLLMOutput" with the content from data.result
                document.getElementById('defaultRAGOutput').textContent = data.result;
                document.getElementById('ragElectrictiy').textContent = "Stromverbrauch: " + data.electricity + " mWh";

                // Set button back to green
                const button = document.getElementById('sendData');
                button.textContent = 'Eingabe';
                button.classList.remove('bg-gray-300');
                button.classList.add('bg-green-500');
                button.classList.add('hover:bg-green-600');
            }
        })
        .catch((error) => {
            console.error('Status Check Error:', error); // Log any errors to the console
            clearInterval(statusInterval); // Ensure interval is cleared on error to prevent infinite loop
        });
    }, 2000); // Check every 2000 milliseconds (2 seconds)
}