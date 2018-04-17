axios.defaults.withCredentials = true
vm = new Vue({
    el: "#app",
    data: {
        page: 'dashboard', // dashboard | server_manage | application_manage | login | logout
        loginState: false,
        serversList: [],
        appsList: [],
        _serverId: -1
    },
    created() {
        this.getServers()
        this.getApps()
        axios.get("/is_login").then(res => {
            if (res.data.data) this.loginState = true
        })
    },
    methods: {
        getServers() {
            axios.get("/servers").then(res => this.serversList = res.data.data)
        },
        getApps() {
            axios.get("/apps").then(res => this.appsList = res.data.data)
        },
        appsOfServer(serverId) {
            return this.appsList.filter(e => e.server_id == serverId)
        },
        login() {
            axios.post("/login",
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
                axios.post("/logout").then(res => this.loginState = false)
            }
        },
        addServer() {
            axios.post("/servers",
                {
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
                }).catch(res => alert("Add failed"))
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
            $('#add-app').modal('show')
            $('#add-app-server').val(this.serversList.filter(e => e.id === server_id)[0].address)
            this._serverId = server_id
        },
        addApp() {
            axios.post("/apps",
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
            return false;
        }
    }
})