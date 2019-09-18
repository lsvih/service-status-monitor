axios.defaults.withCredentials = true
vm = new Vue({
    el: "#app",
    data: {
        page: 'dashboard', // dashboard | server_manage | application_manage | login | logout
        loginState: false,
        serversList: [],
        appsList: [],
        gpuServersList: [],
        _serverId: -1,
        _appId: -1,
        opt: ''
    },
    created() {
        if (window.location.hash === "#dashboard")
            this.page = 'dashboard'
        else if (window.location.hash === "#gpu")
            this.page = 'gpu'
        this.getServers()
        this.getApps()
        setTimeout(() => this.getGPUServers(), 100)
        setInterval(() => {
            this.getServers()
            this.getApps()
            this.getGPUServers()
        }, 20000)
        axios.get("/is_login/").then(res => {
            if (res.data.data) this.loginState = true
        })
    },
    methods: {
        getServers() {
            axios.get("/servers/").then(res => this.serversList = res.data.data)
        },
        getApps() {
            axios.get("/apps/").then(res => this.appsList = res.data.data)
        },
        getGPUServers() {
            axios.get("/get_gpu_status").then(res => this.gpuServersList = res.data.data)
            setTimeout(this.updateProgressbar, 100)
        },
        appsOfServer(serverId) {
            return this.appsList.filter(e => e.server_id == serverId)
        },
        login() {
            axios.post("/login/",
                {username: $('#inputName').val(), password: $('#inputPassword').val()})
                .then(res => {
                    if (res.data.data === 'success') {
                        this.loginState = true
                        $('#inputName').val('')
                        $('#inputPassword').val('')
                        $('#login').modal("hide")
                    } else
                        alert("Login failed")
                }).catch(res => alert("Login failed"))
            return false;
        },
        logout() {
            if (confirm("Confirm logout?")) {
                axios.post("/logout/").then(res => this.loginState = false)
            }
        },
        optServer() {
            if (this.opt === 'addServer') {
                axios.post("/servers/",
                    {
                        name: $('#add-server-name').val(),
                        description: $('#add-server-des').val(),
                        address: $('#add-server-ip').val(),
                        cycle: $('#add-server-cycle').val(),
                        state: Number($('#add-server-check')[0].checked),
                        gpu: Number($('#add-gpu-server-check')[0].checked)
                    })
                    .then(res => {
                        $('#add-server-name').val("")
                        $('#add-server-des').val("")
                        $('#add-server-ip').val("")
                        $('#add-server-cycle').val("1")
                        this.getServers()
                        $('#add-server').modal('hide')
                    }).catch(res => alert("Add failed"))
            } else if (this.opt === 'editServer') {
                axios.put(`/servers/`,
                    {
                        id: this._serverId,
                        name: $('#add-server-name').val(),
                        description: $('#add-server-des').val(),
                        address: $('#add-server-ip').val(),
                        cycle: $('#add-server-cycle').val(),
                        state: Number($('#add-server-check')[0].checked),
                        gpu: Number($('#add-gpu-server-check')[0].checked)
                    })
                    .then(res => {
                        $('#add-server-name').val("")
                        $('#add-server-des').val("")
                        $('#add-server-ip').val("")
                        $('#add-server-cycle').val("1")
                        this.getServers()
                        $('#add-server').modal('hide')
                    }).catch(res => alert("Edit failed"))
            }
            return false;
        },
        deleteServer(id) {
            if (this.appsOfServer(id).length > 0) {
                alert("Must delete sub-applications of this server.")
            } else {
                if (confirm("Confirm delete this server?")) {
                    axios.delete(`/servers/${id}`)
                        .then(res => {
                            this.getServers()
                        }).catch(res => alert("Delete failed"))
                }
            }
        },
        deleteApp(id) {
            if (confirm("Confirm delete this app?")) {
                axios.delete(`/apps/${id}`)
                    .then(res => {
                        this.getApps()
                    }).catch(res => alert("Delete failed"))
            }
        },
        openAddAppPanel(server_id) {
            this.opt = 'addApp'
            $('#add-app-name').val('')
            $('#add-app-address').val('')
            $('#add-app-des').val('')
            $('#add-app-path').val('')
            $('#add-app-cycle').val(1)
            $('#add-app-check')[0].checked = false
            $('#add-app-server').val(this.serversList.filter(e => e.id === server_id)[0].address)
            $('#add-app').modal('show')
            this._serverId = server_id
        },
        openEditAppPanel(app_id) {
            this.opt = 'editApp'
            let app = this.appsList.filter(e => e.id === app_id)[0]
            $('#add-app-name').val(app.name)
            $('#add-app-address').val(app.address.replace('http://', ''))
            $('#add-app-des').val(app.description)
            $('#add-app-path').val(app.project_path)
            $('#add-app-cycle').val(app.cycle)
            $('#add-app-check')[0].checked = app.state === 1
            $('#add-app-server').val(this.serversList.filter(e => e.id === app.server_id)[0].address)
            $('#add-app').modal('show')
            this._appId = app_id
        },
        optApp() {
            if (this.opt === 'addApp') {
                axios.post("/apps/",
                    {
                        name: $('#add-app-name').val(),
                        address: `http://${$('#add-app-address').val()}`,
                        description: $('#add-app-des').val(),
                        project_path: $('#add-app-path').val(),
                        server_id: this._serverId,
                        cycle: $('#add-app-cycle').val(),
                        state: Number($('#add-app-check')[0].checked)
                    })
                    .then(res => {
                        $('#add-app-name').val("")
                        $('#add-app-des').val("")
                        $('#add-app-address').val("")
                        $('#add-app-path').val("")
                        $('#add-app-cycle').val("1")
                        this.getApps()
                        this._serverId = -1
                        $('#add-app').modal('hide')
                    }).catch(res => alert("Add failed"))
            } else if (this.opt === 'editApp') {
                axios.put("/apps/",
                    {
                        id: this._appId,
                        name: $('#add-app-name').val(),
                        address: `http://${$('#add-app-address').val()}`,
                        description: $('#add-app-des').val(),
                        project_path: $('#add-app-path').val(),
                        cycle: $('#add-app-cycle').val(),
                        state: Number($('#add-app-check')[0].checked)
                    })
                    .then(res => {
                        $('#add-app-name').val("")
                        $('#add-app-des').val("")
                        $('#add-app-address').val("")
                        $('#add-app-path').val("")
                        $('#add-app-cycle').val("1")
                        this.getApps()
                        this._appId = -1
                        $('#add-app').modal('hide')
                    }).catch(res => alert("Edit failed"))
            }
            return false;
        },
        openEditServerPanel(server_id) {
            this.opt = 'editServer'
            $('#add-server').modal('show')
            let server = this.serversList.filter(e => e.id === server_id)[0]
            $('#add-server-name').val(server.name)
            $('#add-server-des').val(server.description)
            $('#add-server-ip').val(server.address)
            $('#add-server-cycle').val(server.cycle)
            $('#add-server-check')[0].checked = server.state === 1
            $('#add-gpu-server-check')[0].checked = server.gpu === 1
            this._serverId = server_id
        },
        openAddServerPanel() {
            this.opt = 'addServer'
            $('#add-server').modal('show')
            $('#add-server-name').val("")
            $('#add-server-des').val("")
            $('#add-server-ip').val("")
            $('#add-server-cycle').val(1)
            $('#add-server-check')[0].checked = false
            $('#add-gpu-server-check')[0].checked = false
        },
        memoryStringToNumber(memoryStr) {
            return memoryStr.match(/\d+/g)
        },
        updateProgressbar() {
            $(".circle-progress").each(function () {
                let value = $(this).attr('data-value');
                let left = $(this).find('.progress-left .progress-bar');
                let right = $(this).find('.progress-right .progress-bar');
                if (value > 0) {
                    if (value <= 50) {
                        right.css('transform', 'rotate(' + percentageToDegrees(value) + 'deg)')
                    } else {
                        right.css('transform', 'rotate(180deg)')
                        left.css('transform', 'rotate(' + percentageToDegrees(value - 50) + 'deg)')
                    }
                }
            })

            function percentageToDegrees(percentage) {
                return percentage / 100 * 360
            }
        }
    }
})