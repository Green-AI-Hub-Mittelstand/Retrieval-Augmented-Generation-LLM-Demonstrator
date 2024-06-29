document.getElementById('sendDataUrl').addEventListener('click', function() {
    const userInput = document.getElementById('userInput').value; // Get the user input value

    // Define the data to be sent in the request body
    const data = { input: userInput };

    // Use fetch to send a POST request to the /submit endpoint
    fetch('/submitwiki', {
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
        checkDatabaseStatus(taskId); // Call function to periodically check task status
    })
    .catch((error) => {
        console.error('Submit Error:', error); // Log any errors to the console
    });
});

function checkDatabaseStatus(taskId) {
    const statusInterval = setInterval(() => {
        fetch(`/status/database/${taskId}`) // Use template literals to include taskId in the URL
        .then(response => response.json())
        .then(data => {
            console.log('Checking status:', data); // Log the status check
            if (data.status === 'COMPLETE') { // Check if the task status is 'completed'
                clearInterval(statusInterval); // Stop the interval checks
                console.log('Database add Completed:', data); // Log task completion and any data
                
                // Update the input text field value
                document.getElementById('userInput').value = 'Done!';

                // Hide the message after three seconds
                setTimeout(() => {
                    userInput.value = ''; // Clear the input text field value
                }, 3000);
                
            }
        })
        .catch((error) => {
            console.error('Status Check Error:', error); // Log any errors to the console
            clearInterval(statusInterval); // Ensure interval is cleared on error to prevent infinite loop
        });
    }, 2000); // Check every 2000 milliseconds (2 seconds)
}