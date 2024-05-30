document.addEventListener('DOMContentLoaded', function () {
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');
    const logContent = document.getElementById('log-content');
    const video = document.getElementById('video');
    const toggleButton = document.getElementById('toggleButton');
    const testButton = document.getElementById('testButton');
    const textResult = document.getElementById('textResult');
    const textObjectdetectionResult = document.getElementById('textObjectDetectionResult');
    const textFiredetectionResult = document.getElementById('textFireDetectionResult');
    let cameraOn = false;
    const toggleObjectdetection = document.getElementById('toggle-objectdetection');
    const toggleFiredetection = document.getElementById('toggle-firedetection');

    var eventHandled = {};

    toggleObjectdetection.addEventListener('click', function(event) {
        console.log('Clicked:', event);;
        handleToggleChange('toggleObjectdetection', toggleObjectdetection.checked);
    });

    toggleFiredetection.addEventListener('click', function(event) {
        handleToggleChange('toggleFiredetection', toggleFiredetection.checked);
    });

    function handleToggleChange(toggleId, state) {
        if (eventHandled[toggleId]) {
            return;
        }
        $.ajax({
            url: '/toggle',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                toggleId: toggleId,
                state: state
            }),
            success: function(response) {
                console.log(response.message);
                eventHandled[toggleId] = true;
            },
            error: function(xhr, status, error) {
                console.error('Error:', error);
            }
        });
    }

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            if (tab.getAttribute('id') === 'liveViewTab' && !tab.classList.contains('enabled')) {
                return;
            }
            document.querySelector('.tab.active').classList.remove('active');
            tab.classList.add('active');
            const activeTabContent = document.querySelector('.tab-content.active');
            if (activeTabContent) {
                activeTabContent.classList.remove('active');
            }
            const target = tab.getAttribute('data-tab');
            document.getElementById(target).classList.add('active');
            if (tab.getAttribute('id') === 'logViewTab') {
                loadLogs();
            }
        });
    });

    toggleButton.addEventListener('click', function(event) {
        event.preventDefault();
        if (cameraOn) {
            fetch('/control_camera', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ action: 'stop' })
            }).then(response => response.json()).then(data => {
                if (data.success) {
                    video.style.display = 'none';
                    video.src = '#';
                    toggleButton.textContent = 'Start Streaming';
                    cameraOn = false;
                }
            });
        } else {
            fetch('/control_camera', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ action: 'start' })
            }).then(response => response.json()).then(data => {
                if (data.success) {
                    video.src = '/video_feed';
                    video.style.display = 'block';
                    toggleButton.textContent = 'Stop Streaming';
                    cameraOn = true;
                }
            });
        }
    });

    testButton.addEventListener('click', function(event) {
        event.preventDefault();
        fetch('/test').then(response => response.json()).then(data => {
            console.log(data);
            textResult.textContent = data.result + " Action :" + data.action;
        });
    });

    const cpuGaugeCtx = document.getElementById('cpuGauge').getContext('2d');
    const diskGaugeCtx = document.getElementById('diskGauge').getContext('2d');
    const cpuGauge = new Chart(cpuGaugeCtx, {
        type: 'doughnut',
        data: {
            labels: ['Used', 'Free'],
            datasets: [{
                data: [0, 100],
                backgroundColor: ['#ff6384', '#36a2eb'],
                hoverBackgroundColor: ['#ff6384', '#36a2eb']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    enabled: false
                }
            },
            cutout: '70%',
            rotation: -90,
            circumference: 180
        }
    });

    const diskGauge = new Chart(diskGaugeCtx, {
        type: 'doughnut',
        data: {
            labels: ['Used', 'Free'],
            datasets: [{
                data: [0, 100],
                backgroundColor: ['#ff6384', '#36a2eb'],
                hoverBackgroundColor: ['#ff6384', '#36a2eb']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    enabled: false
                }
            },
            cutout: '70%',
            rotation: -90,
            circumference: 180
        }
    });

    function updateGauges() {
        fetch('/system_stats')
            .then(response => response.json())
            .then(data => {
                cpuGauge.data.datasets[0].data[0] = data.cpu_usage;
                cpuGauge.data.datasets[0].data[1] = 100 - data.cpu_usage;
                cpuGauge.update();

                diskGauge.data.datasets[0].data[0] = data.disk_usage_percent;
                diskGauge.data.datasets[0].data[1] = 100 - data.disk_usage_percent;
                diskGauge.update();

                document.getElementById('cpuValue').innerText = `${data.cpu_usage}%`;
                document.getElementById('diskValue').innerText = `${data.disk_free.toFixed(2)}GB/${data.disk_total.toFixed(2)}GB (${data.disk_usage_percent}%)`;
            });
    }

    function loadLogs() {
        fetch('/get_log')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                logContent.textContent = data.log;
            })
            .catch(error => {
                logContent.textContent = 'Error loading logs';
                console.error('There has been a problem with your fetch operation:', error);
            });
    }

    function updateResult() {
        fetch('/get_detection_result')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.mp_detection_result)
                    textObjectdetectionResult.textContent = "偵測到人員";
                if (data.yolo_detection_result)
                    textFiredetectionResult.textContent = "偵測到火災";
            })
            .catch(error => {
                // textResult.textContent = 'Error loading result';
                console.error('There has been a problem with your fetch operation:', error);
            });
    }

    //setInterval(updateGauges, 10000);
    setInterval(function() {
        if (document.getElementById('log-view').classList.contains('active')) {
            loadLogs();
        }
        updateGauges();
        updateResult();
    }, 2000);
    updateGauges();

    // Login modal logic
    const loginModal = document.getElementById("loginModal");
    const loginButton = document.getElementById("loginButton");
    const closeButton = document.getElementsByClassName("close")[0];
    const confirmButton = document.getElementById("confirmButton");
    const cancelButton = document.getElementById("cancelButton");
    const liveViewTab = document.getElementById("liveViewTab");

    loginButton.onclick = function() {
        if (loginButton.innerText === "登出") {
            if (confirm("確定要登出嗎？")) {
                fetch('/logout')
                .then(response => {
                    if (response.ok) {
                        document.getElementById("loginText").innerText = "未登入";
                        loginButton.innerText = "登入";
                        liveViewTab.classList.remove('enabled');
                        liveViewTab.style.pointerEvents = "none";
                        liveViewTab.style.color = "gray";
                    }
                });
            }
        } else {
            loginModal.style.display = "block";
        }
    }

    closeButton.onclick = function() {
        loginModal.style.display = "none";
    }

    cancelButton.onclick = function() {
        loginModal.style.display = "none";
    }

    confirmButton.onclick = function() {
        const username = document.getElementById("username").value;
        const password = document.getElementById("password").value;

        fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username: username, password: password })
        })
        .then(response => response.json())
        // .then(response => {
        //     if (!response.ok) {
        //         throw new Error('Network response was not ok');
        //     }
        //     return response.json(); // Ensure this is JSON
        // })
        .then(data => {
            console.log(data); // Log the data to check its structure
            if (data.success) {
                document.getElementById("loginText").innerText = "已登入 (使用者: admin)";
                loginButton.innerText = "登出";
                loginModal.style.display = "none";
                liveViewTab.classList.add('enabled');
                liveViewTab.style.pointerEvents = "auto";
                liveViewTab.style.color = "black";
                //window.location.reload();
            } else {
                alert("登入失敗，請檢查您的用戶名和密碼。");
            }
        })
        .catch(error => {
            console.error('There was a problem with the fetch operation:', error);
        });;

        // if (username === "admin" && password === "password") {
        //     document.getElementById("loginText").innerText = "已登入 (使用者: admin)";
        //     loginButton.innerText = "登出";
        //     loginModal.style.display = "none";
        //     liveViewTab.classList.add('enabled');
        //     liveViewTab.style.pointerEvents = "auto";
        //     liveViewTab.style.color = "black";
        // } else {
        //     alert("登入失敗，請檢查您的用戶名和密碼。");
        // }
    }

    // window.onclick = function(event) {
    //     if (event.target === loginModal) {
    //         loginModal.style.display = "none";
    //     }
    // }

    // Initially disable live view tab
    liveViewTab.classList.remove('enabled');
    liveViewTab.style.pointerEvents = "none";
    liveViewTab.style.color = "gray";
});

// $(document).ready(function(){
//     $('.tab-content').hide();
//     $('.tab-content:first').addClass('current').show();

//     $('.tab').click(function() {
//         var tab_id = $(this).attr('data-tab');

//         $('.tab').removeClass('active');
//         $('.tab-content').removeClass('current').hide();

//         $(this).addClass('active');
//         $("#" + tab_id).addClass('current').show();

//         if (tab_id === 'log-view') {
//             loadLogs();
//         }
//     });

//     function loadLogs() {
//         $.ajax({
//             url: '/get_log',
//             method: 'GET',
//             success: function(data) {
//                 $('#log-content').text(data.log);
//             },
//             error: function() {
//                 $('#log-content').text('Error loading logs');
//             }
//         });
//     }

//     // Auto-refresh logs every 10 seconds
//     setInterval(function(){
//         if ($('#log-view').hasClass('current')) {
//             loadLogs();
//         }
//     }, 10000);
// });
