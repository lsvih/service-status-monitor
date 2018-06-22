axios.defaults.withCredentials = true
vm = new Vue({
    el: "#app",
    data: {
        page: 'dashboard', // dashboard | server_manage | application_manage | login | logout
        loginState: false,
        serversList: [],
        appsList: [],
        _serverId: -1,
        _appId: -1,
        opt: ''
    },
    created() {
        this.getServers()
        this.getApps()
        axios.get("/api/is_login/").then(res => {
            if (res.data.data) this.loginState = true
        })
    },
    methods: {
        getServers() {
            axios.get("/api/servers/").then(res => this.serversList = res.data.data)
        },
        getApps() {
            axios.get("/api/apps/").then(res => this.appsList = res.data.data)
        },
        appsOfServer(serverId) {
            return this.appsList.filter(e => e.server_id == serverId)
        },
        login() {
            axios.post("/api/login/",
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
                axios.post("/api/logout/").then(res => this.loginState = false)
            }
        },
        optServer() {
            if (this.opt === 'addServer') {
                axios.post("/api/servers/",
                    {
                        name: $('#add-server-name').val(),
                        description: $('#add-server-des').val(),
                        address: $('#add-server-ip').val(),
                        cycle: $('#add-server-cycle').val(),
                        state: Number($('#add-server-check')[0].checked),
                        username: $('#username').val(),
                        password: $('#password').val()
                    })
                    .then(res => {
                        $('#add-server-name').val("")
                        $('#add-server-des').val("")
                        $('#add-server-ip').val("")
                        $('#add-server-cycle').val("1")
                        $('#username').val('')
                        $('#password').val('')
                        this.getServers()
                        $('#add-server').modal('hide')
                    }).catch(res => alert("Add failed"))
            } else if (this.opt === 'editServer') {
                axios.put(`/api/servers/`,
                    {
                        id: this._serverId,
                        name: $('#add-server-name').val(),
                        description: $('#add-server-des').val(),
                        address: $('#add-server-ip').val(),
                        cycle: $('#add-server-cycle').val(),
                        state: Number($('#add-server-check')[0].checked)
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
                    axios.delete(`/api/servers/${id}`)
                        .then(res => {
                            this.getServers()
                        }).catch(res => alert("Delete failed"))
                }
            }
        },
        deleteApp(id) {
            if (confirm("Confirm delete this app?")) {
                axios.delete(`/api/apps/${id}`)
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
                axios.post("/api/apps/",
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
                axios.put("/api/apps/",
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
        },
    }
})