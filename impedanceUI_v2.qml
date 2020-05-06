import QtQuick 2.12
import QtQuick.Window 2.2
import QtQuick.Layouts 1.2
import QtQuick.Controls 2.12
import QtQuick.Dialogs 1.2
import QtQuick.Controls.Styles 1.4
import QtWebEngine 1.8

ApplicationWindow {
    id: mainView
    visible: true

    width: 700
    height: 800
    minimumWidth: 700
    minimumHeight: 800
    title: qsTr("Phy-EIS by Thuy Linh Pham")

    property int lastW: 0
    property int lastH: 0


	// Full cell DX22 + LR_DX30_Cd_becomes_C_//(DE6_Cs)
    property var phy_eis_names: ["L", "R", "R_OHM", "DX22_R1", "DX22_R2", "DX22_T2", "DX22_P2", "DX22_R3", "DX22_T3", "DX22_P3", "Rm", "Rct", "Rd", "Cdl_C0", "Cdl_HNC", "Cdl_HNT", "Cdl_HNP", "Cdl_HNU", "Cd_C0", "Cd_Cs","DE6_d_R", "DE6_d_T", "DE6_d_P", "DE6_d_U", "CPE_B_T", "CPE_B_P"]
    property var phy_eis_values: ["2.0717e-7", "1.2565e-7", "6.314", "1e-20", "1e20", "1e-20", "1e-20", "0.1", "0.1", "1", "34.68", "22.29", "27.37", "5.1388e-6", "3.542e-5", "0.0003955", "1.0", "0.75983", "0.048411", "1e-5","0.97414", "134.9", "1.0", "1.0", "0.023301", "0.5"]
    property var phy_eis_fixed: [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
	

    property string dialogCreated: ""

    property real pressX: 0.0
    property real pressY: 0.0
    property real releaseX: 0.0
    property real releaseY: 0.0
    property bool pressHold: false

    property string ls_data: ""
    property string savedType: ""
    signal switchToggled(string switchName, bool ischecked)
    signal fitClicked(int wgting, int fitmethod)
    signal simulationClicked

    MessageDialog {
        id: fitStatusDialog
        title: "Data for fitting"
        text: "Please choose model correctly"
        icon: StandardIcon.Warning
    }

    MessageDialog {
        id: fit_report
        title: "Fit Report"
        text: ""
        icon: StandardIcon.Information
        modality: Qt.NonModal
    }

    onSwitchToggled: {
        console.log(switchName, ischecked)
        var val_name = switchName.replace("fixed", "val")
        console.log(gridDialog.children.length)
        for (var i = 1; i < gridDialog.children.length; i++) {
            console.log(gridDialog.children[i].children[0].children[0].text.toLowerCase(
                            ))
            if (gridDialog.children[i].children[0].children[0].text.toLowerCase(
                        ) + '_val' == val_name) {
                console.log(ischecked, i)

                if (ischecked) {
                    gridDialog.children[i].children[1].children[0].readOnly = false
                    gridDialog.children[i].children[1].children[0].selectByMouse = true
                    gridDialog.children[i].children[1].children[0].cursorPosition = 0
                } else {
                    gridDialog.children[i].children[1].children[0].readOnly = true
                    gridDialog.children[i].children[1].children[0].selectByMouse = false
                    gridDialog.children[i].children[1].children[0].cursorPosition = 0
                }
                break
            }
        }
    }

    Connections {
        target: impedance

        onPlotStringSignal: {
            graphView.url = ""
            console.log('plotURL: ', plotHtmlString)
            graphView.url = plotHtmlString
            saveFitResults.enabled = true
            console.log(graphView.url)
        }

        onParamsZfitEmit: {
            console.log("Fit Completed")
            updateValues(param_names, best_params, error_fit, error_fit_percent)
        }

        onLoadParamsEmit:   {
           console.log("Load parameters")
           loadValues(param_names, best_params, error_fit, error_fit_percent, par_frees)
        }

        onCapacitanceEmit: {
            console.log("Capacitance emited")
        }

        onAdmittanceEmit: {
            console.log("Admitance emited")
        }

        onFitStatus: {
            fittingBtn.text = "Fit"
            if (fit_status == 1) {
                fitStatus.text = "Success"
                console.log("Fit succeeded")
                saveParameters.enabled = true
                saveFitResults.enabled = true
            } else {
                saveParameters.enabled = false
                saveFitResults.enabled = false
                if (fit_status == 0) {
                    fitStatus.text = "Failed"
                    console.log("Fit failed")
                } else {
                    fitStatus.text = "Stopped"
                    console.log("Fit stopped")
                }
            }
        }

        onChiSquare: {
            chisqr.text = chiSquare_Val
            redChisqr.text = redChiSquare_Val
            residual.text = residual_Val
        }

        onSimulationEmit: {
            console.log("Simulation Completed")
        }

        onFitReport: {
            fit_report.text = fitReportStr
            //fit_report.open()
        }

        onFitLog: {
            console.log("LOG: " + fit_log)
            fit_log_text.text = fit_log
        }

        onFitCompleted: {

            //            console.log("Recv params: ", new_params, fit_ret)
        }
    }

    // Load initial values
    function loadValues(param_names, best_params, error_fit, error_fit_percent, par_frees) {
        console.log("Load values")
        console.log(best_params)
		for (var pj = 1; pj < gridDialog.children.length; pj++) {
			for (var i = 1; i <= param_names.length; i++) {
				console.log('CK :', pj, gridDialog.children.length, gridDialog.children[pj].children[0].children[0].text, param_names[i-1])
				if (gridDialog.children[pj].children[0].children[0].text.toLowerCase() === param_names[i-1].toLowerCase())  {
					gridDialog.children[pj].children[1].children[0].text = best_params[i - 1]
					gridDialog.children[pj].children[1].children[0].cursorPosition = 0
					gridDialog.children[pj].children[3].children[0].text = error_fit[i - 1]
					gridDialog.children[pj].children[4].children[0].text = error_fit_percent[i - 1]

					if (par_frees[i-1] === 1)    {
						gridDialog.children[pj].children[2].checked = true
					}
					else    {
						gridDialog.children[pj].children[2].checked = false
					}
					console.log('Assign :', pj, gridDialog.children.length, gridDialog.children[pj].children[0].children[0].text, param_names[i])
					break
				}
			}
		}
    }

    // Update parameter values after fitting
    function updateValues(param_names, best_params, error_fit, error_fit_percent) {
        for (var i = 1; i <= param_names.length; i++) {
            gridDialog.children[i].children[1].children[0].text = best_params[i - 1]
            gridDialog.children[i].children[1].children[0].cursorPosition = 0
            gridDialog.children[i].children[3].children[0].text = error_fit[i - 1]
            //            gridDialog.children[i].children[3].width = gridDialog.children[i].children[3].children[0].paintedWidth
            gridDialog.children[i].children[4].children[0].text = error_fit_percent[i - 1]
            //            console.log(best_params[i])
        }
    }

    function createDialogParameters(model_name, param_names, param_values, param_fixed) {
        fittingSimulationDialog.title = model_name + " Fitting/Simulation"
        //        console.log(model_name, " selected")
        if (dialogCreated === model_name) {
            console.log(dialogCreated, model_name)
        } else {
            for (var igd = gridDialog.children.length; igd > 0; igd--)
                gridDialog.children[igd - 1].destroy()

            var str_header = 'import QtQuick 2.12; import QtQuick.Controls 2.5; import QtQuick.Layouts 1.2; RowLayout{ spacing: 10; Rectangle {width:50;height:20;color:"transparent"; Text { text:"' + "Element"
                    + '";font.pixelSize: 12;anchors.left: parent.left;anchors.bottom:parent.bottom;anchors.right:parent.right;bottomPadding:2; }} Rectangle {width:100;height:20; Text {text: "' + "Value"
                    + '"; clip: true;font.pixelSize: 12;anchors.left: parent.left;anchors.bottom:parent.bottom;anchors.right:parent.right;leftPadding: 5;rightPadding:5; bottomPadding:2}} Rectangle {width:50;height:20;color:"transparent"; Text { text:"' + "Fix/Free"
                    + '";font.pixelSize: 12;clip: true; anchors.left: parent.left;anchors.bottom:parent.bottom;anchors.right:parent.right;bottomPadding:2; }}  Rectangle {width:150;height:20;color:"transparent"; Text { text:"' + "Error"
                    + '";font.pixelSize: 12;clip: true; anchors.left: parent.left;anchors.bottom:parent.bottom;anchors.right:parent.right;bottomPadding:2; }} Rectangle {width:150;height:20;color:"transparent"; Text { text:"' + "Error %"
                    + '";font.pixelSize: 12; clip: true; anchors.left: parent.left;anchors.bottom:parent.bottom;anchors.right:parent.right;bottomPadding:2; }}}'
            try {
                Qt.createQmlObject(str_header, gridDialog, 'CustomObject')
            } catch (err) {
                console.log('Error on line ' + err.qmlErrors[0].lineNumber
                            + '\n' + err.qmlErrors[0].message)
            }
            gridDialog.rows = param_names.length + 1
            gridDialog.columns = 1
            dialogCreated = model_name
            for (var i = 0; i < param_names.length; i++) {
                var str_object = 'import QtQuick 2.12; import QtQuick.Controls 2.5; import QtQuick.Layouts 1.2; RowLayout{ spacing: 10; Rectangle {width:50;height:20;color:"transparent"; Text { text:"' + param_names[i] + '";font.pixelSize: 12;anchors.left: parent.left;anchors.bottom:parent.bottom;anchors.right:parent.right;bottomPadding:2; }} Rectangle {width:100;height:20;color: "white";border.color:"black"; TextInput {id:'
                        + param_names[i].toLowerCase() + "_val" + '; text: "'
                        + param_values[i] + '"; readOnly:true; cursorVisible: false; selectionColor: "green";selectByMouse: false;clip: true;font.pixelSize: 12;anchors.left: parent.left;anchors.bottom:parent.bottom;leftPadding: 5;rightPadding:5; bottomPadding:2; width:95}} Switch {id: ' + param_names[i].toLowerCase() + '_fixed; indicator: Rectangle {implicitWidth: 20; implicitHeight: 10; x: parent.leftPadding; y: parent.height / 2 - height / 2; radius: 5; color: parent.checked ? "#17a81a" : "#ffffff"; border.color: parent.checked ? "#17a81a" : "#cccccc"; Rectangle {x: parent.parent.checked ? parent.width - width : 0;width: 10;height: 10;radius: 5;color: parent.parent.down ? "#cccccc" : "#ffffff";border.color: parent.parent.checked ? (parent.parent.down ? "#17a81a" : "#21be2b") : "#999999"}} onToggled:{mainView.switchToggled("' + param_names[i].toLowerCase(
                            ) + '_fixed", checked)}} Rectangle {width:150;height:20;color:"transparent"; Text { text:"' + "" + '";font.pixelSize: 12;clip: true; anchors.left: parent.left;anchors.bottom:parent.bottom;anchors.right:parent.right;bottomPadding:2; }} Rectangle {width:150;height:20;color:"transparent"; Text { text:"' + "" + '";font.pixelSize: 12; clip: true; anchors.left: parent.left;anchors.bottom:parent.bottom;anchors.right:parent.right;bottomPadding:2; }}}'
                //console.log(str_object)
                try {
                    Qt.createQmlObject(str_object, gridDialog, 'CustomObject')
                } catch (err) {
                    console.log('Error on line ' + err.qmlErrors[0].lineNumber
                                + '\n' + err.qmlErrors[0].message)
                }
            }
        }
    }

    function resetDialogParameters(param_names, param_values) {
        console.log("Reset initial values")
        for (var i = 1; i <= param_names.length; i++) {
            gridDialog.children[i].children[1].children[0].text = param_values[i - 1]
            gridDialog.children[i].children[1].children[0].cursorPosition = 0
        }
    }
    AbstractDialog {
        id: fittingSimulationDialog
        title: "Run Fitting/Simulation"
        modality: Qt.NonModal
        standardButtons: Dialog.NoButton

        contentItem: Rectangle {
            implicitWidth: dgl.childrenRect.width + 20
            implicitHeight: dgl.childrenRect.height + 20

            GridLayout {
                columns: 2
                rows: 3
                id: dgl
                RowLayout {
                    Layout.margins: 10
                    spacing: 10
                    Layout.row: 0
                    Layout.columnSpan: 2
                    ComboBox {
                        id: wgtMethod
                        model: ["Unit", "Data proportional", "Calc proportional", "Data Modulus", "Calc modulus"]
                        ToolTip.text: "Weighting Method"
                        ToolTip.visible: hovered
                        implicitWidth: 115
                        currentIndex: 4
                        background: Rectangle {
                            border.color: "black"
                            border.width: 2
                            radius: 3
                            width: parent.width - 10
                        }
                    }
                    ComboBox {
                        id: fitMethod
                        model: ["least_squares"]
                        ToolTip.text: "Fitting Method"
                        ToolTip.visible: hovered
                        implicitWidth: 130
                        currentIndex: 0
                        background: Rectangle {
                            border.color: "black"
                            border.width: 2
                            radius: 3
                            width: parent.width - 10
                        }
                    }

                    Rectangle {
                        width: 50
                        height: fitMethod.height
                        color: "transparent"
                        Text {
                            text: "Status:"
                            font.pixelSize: 12
                            anchors.left: parent.left
                            anchors.bottom: parent.bottom
                            anchors.right: parent.right
                            bottomPadding: 2
                        }
                    }

                    Rectangle {
                        width: 50
                        height: fitMethod.height
                        color: "transparent"
                        Text {
                            id: fitStatus
                            text: ""
                            font.pixelSize: 12
                            anchors.left: parent.left
                            anchors.bottom: parent.bottom
                            anchors.right: parent.right
                            bottomPadding: 2
                        }
                    }
                    Rectangle {
                        width: 50
                        height: fitMethod.height
                        color: "transparent"
                        Text {
                            text: "Chi-square:"
                            font.pixelSize: 12
                            anchors.left: parent.left
                            anchors.bottom: parent.bottom
                            anchors.right: parent.right
                            bottomPadding: 2
                        }
                    }

                    Rectangle {
                        width: 100
                        height: fitMethod.height
                        Layout.leftMargin: 5
                        color: "transparent"
                        Text {
                            id: chisqr
                            text: ""
                            font.pixelSize: 12
                            anchors.left: parent.left
                            anchors.bottom: parent.bottom
                            anchors.right: parent.right
                            bottomPadding: 2
                            clip: true
                        }
                    }

                    Rectangle {
                        width: 100
                        height: fitMethod.height
                        color: "transparent"
                        Text {
                            text: "Reduced-chiSquare:"
                            font.pixelSize: 12
                            anchors.left: parent.left
                            anchors.bottom: parent.bottom
                            anchors.right: parent.right
                            bottomPadding: 2
                        }
                    }

                    Rectangle {
                        width: 100
                        height: fitMethod.height
                        Layout.leftMargin: 5
                        color: "transparent"
                        Text {
                            id: redChisqr
                            text: ""
                            font.pixelSize: 12
                            anchors.left: parent.left
                            anchors.bottom: parent.bottom
                            anchors.right: parent.right
                            bottomPadding: 2
                            clip: true
                        }
                    }

                    Rectangle {
                        width: 50
                        height: fitMethod.height
                        color: "transparent"
                        Text {
                            text: "Residual:"
                            font.pixelSize: 12
                            anchors.left: parent.left
                            anchors.bottom: parent.bottom
                            anchors.right: parent.right
                            bottomPadding: 2
                        }
                    }

                    Rectangle {
                        width: 100
                        height: fitMethod.height
                        Layout.leftMargin: 5
                        color: "transparent"
                        Text {
                            id: residual
                            text: ""
                            font.pixelSize: 12
                            anchors.left: parent.left
                            anchors.bottom: parent.bottom
                            anchors.right: parent.right
                            bottomPadding: 2
                            clip: true
                        }
                    }
                }

                GridLayout {
                    id: gridDialog
                    Layout.row: 1
                    Layout.column: 0
                    Layout.margins: 10
                    columnSpacing: 10
                }

                Rectangle {
                    id: otherOptions
                    Layout.column: 1
                    Layout.row: 1
                    Layout.fillHeight: true
                    Layout.fillWidth: true
                    border {
                        width: 2
                        color: "blue"
                    }
                    GridLayout {
                        width: parent.width
                        height: parent.height
                        columns: 2
                        rows: 2

                        GridLayout {
                            Layout.row: 1
                            Layout.column: 0
                            Layout.columnSpan: 2
                            Layout.fillWidth: true
                            Layout.margins: 10
                            rows: 2
                            columns: 3
                            height: resetParameters.height

                            Button {
                                id: resetParameters
                                text: "Load initial values"
                                padding: 5
                                Layout.maximumHeight: 30
                                //width: 200
                                Layout.fillWidth: true
                                onClicked: {
                                    loadParametersDialog.open()
//                                    resetDialogParameters()
//                                    switch (dataSelect.currentText) {
//                                    case "DX30":
//                                        console.log("DX30 selected")
//                                        resetDialogParameters(dx30_names,
//                                                              dx30_values)
//                                        break
//                                    case "DX29":
//                                        console.log("DX29 selected")
//                                        resetDialogParameters(dx29_names,
//                                                              dx29_values)
//                                        break
//                                    case "Bisquert_General":
//                                        console.log("Bisquert General selected")
//                                        resetDialogParameters(
//                                                    bis_general_name,
//                                                    bis_general_values)
//                                        break
//                                    case "OTM_LSM10":
//                                        console.log("OTM_LSM10 selected")
//                                        resetDialogParameters(otm_lsm10_names,
//                                                              otm_lsm10_values)
//                                        break
//                                    case "LLZ":
//                                        console.log("LLZ selected")
//                                        resetDialogParameters(llz_names,
//                                                              llz_values)
//                                        break
//                                    default:
//                                        console.log("Please select data")
//                                        break
//                                    }
                                }
                            }

                            Button {
                                id: fittingBtn
                                text: "Fit"
                                Layout.maximumHeight: 30
                                //Layout.maximumWidth: 50
                                Layout.fillWidth: true
                                onClicked: {
                                    if (fittingBtn.text == "Stop") {
                                        console.log("Stop fitting")
                                        fitStatus.text = "Stopping"
                                        impedance.stop_fitting()
                                    } else {
                                        if (dataPath.text === "Data Path:"
                                                && ls_data == "") {
                                            fitStatusDialog.text = "Please choose data file, model"
                                            fitStatusDialog.open()
                                        } else {
                                            fitStatus.text = "Running"
                                            var send_names = []
                                            var send_vals = []
                                            var send_fixed = []
                                            var cur_strings = ""
                                            var cur_isFixed = ""
                                            var cur_name = ""
                                            var send_mdl = dataSelect.currentText
                                            var send_data = dataPath.text
                                            var cur_method = fitMethod.currentText
                                            //var niters = maxNumIteration.text
                                            //var pnorm = parnorm.checked ? 1 : 0
                                            //var rm_noise = rmNoise.checked ? 1: 0
                                            for (var i = 1; i < gridDialog.children.length; i++) {
                                                cur_name = gridDialog.children[i].children[0].children[0].text.toLowerCase()
                                                cur_strings = gridDialog.children[i].children[1].children[0].text
                                                cur_isFixed = gridDialog.children[i].children[2].checked ? 0 : 1
                                                send_vals.push(cur_strings)
                                                send_fixed.push(cur_isFixed)
                                                send_names.push(cur_name)
                                            }

                                            if (fileDialog.selectMultiple) {
                                                send_data = ls_data
                                            }

                                            fittingBtn.text = "Stop"
                                            impedance.fitting(
                                                        send_names, send_vals,
                                                        send_fixed, send_mdl,
                                                        wgtMethod.currentIndex,
                                                        fitMethod.currentText,
                                                        send_data, 1, 0)
                                        }
                                    }
                                }
                            }
                            Button {
                                id: simulationBtn
                                text: "Simulation"
                                Layout.maximumHeight: 30
                                //Layout.maximumWidth: 100
                                Layout.fillWidth: true
                                onClicked: {
                                    if (dataPath.text === "Data Path:"
                                            && ls_data == "") {
                                        fitStatusDialog.text = "Please choose data file, model"
                                        fitStatusDialog.open()
                                    } else {
                                        fitStatus.text = "Running"
                                        var send_names = []
                                        var send_vals = []
                                        var send_fixed = []
                                        var cur_strings = ""
                                        var cur_isFixed = ""
                                        var cur_name = ""
                                        var send_mdl = dataSelect.currentText
                                        var send_data = dataPath.text
                                        var cur_method = fitMethod.currentText
                                        for (var i = 1; i < gridDialog.children.length; i++) {
                                            cur_name = gridDialog.children[i].children[0].children[0].text.toLowerCase()
                                            cur_strings = gridDialog.children[i].children[1].children[0].text
                                            cur_isFixed = gridDialog.children[i].children[2].checked ? 0 : 1
                                            send_vals.push(cur_strings)
                                            send_fixed.push(cur_isFixed)
                                            send_names.push(cur_name)
                                        }
                                        impedance.fitting(
                                                    send_names, send_vals,
                                                    send_fixed, send_mdl,
                                                    wgtMethod.currentIndex,
                                                    fitMethod.currentText,
                                                    send_data, 2, 0, 0, 0)
                                    }
                                }
                            }
                            Button {
                                id: saveParameters
                                text: "Save Parameters"
                                Layout.maximumHeight: 30
                                //Layout.maximumWidth: 100
                                Layout.fillWidth: true
                                enabled: false
                                onClicked: {
                                    savedDialog.title = "Save Parameters"
                                    savedType = "parameters"
                                    savedDialog.open()
                                    console.log("Save parameters clicked")
                                }
                            }
                            Button {
                                id: saveFitResults
                                text: "Save Fit Results"
                                Layout.maximumHeight: 30
                                //Layout.maximumWidth: 100
                                Layout.fillWidth: true
                                enabled: false
                                onClicked: {
                                    if (fileDialog.selectMultiple) {
                                        savedDialog.selectFolder = true
                                        savedDialog.selectExisting = true
                                    } else {
                                        savedDialog.selectExisting = false
                                        savedDialog.selectMultiple = false
                                        savedDialog.selectFolder = false
                                    }
                                    savedType = "fitResults"
                                    savedDialog.title = "Save Fit Results"
                                    savedDialog.open()
                                    console.log("saveFitResults clicked")
                                }
                            }
                        }

                        Rectangle {
                            Layout.row: 2
                            Layout.column: 0
                            Layout.columnSpan: 2
                            Layout.fillHeight: true
                            Layout.fillWidth: true
                            Layout.margins: 10
                            border {
                                color: "black"
                                width: 0
                            }
                            clip: true
                            ScrollBar   {
                                anchors.fill: parent
                            }

                            Text {
                                anchors.fill: parent
                                id: fit_log_text
                                text: ""
                                font.pixelSize: 12
                                anchors.margins: 10
                                clip: true
                            }
                        }
                    }
                }

                RowLayout {
                    Layout.alignment: Qt.AlignCenter
                    Layout.preferredHeight: 50
                    Layout.margins: 10
                    Layout.row: 2
                    Layout.columnSpan: 2
                }
            }
        }
    }

    menuBar: MenuBar {
        objectName: "abc"
        Menu {
            title: "File"
            MenuItem {
                text: "Open..."
            }
            MenuItem {
                text: "Close"
            }
        }

        Menu {
            title: "Edit"
            MenuItem {
                text: "Cut"
            }
            MenuItem {
                text: "Copy"
            }
            MenuItem {
                text: "Paste"
            }
        }

        Menu {
            title: "Help"
            MenuItem {
                text: "About"
            }
        }
    }

    MessageDialog {
        id: dataMessageDialog
        title: "Data for fitting"
        text: "Please choose model correctly"
        icon: StandardIcon.Warning
    }

    FileDialog  {
        id: loadParametersDialog
        title: "Select parameters file"
        selectExisting: true
        selectMultiple: false
        selectFolder: false
        modality: Qt.WindowModal
        onAccepted: {
            var cur_path = fileUrl.toString()
            cur_path = cur_path.replace(
                        /^(file:\/{3})|(qrc:\/{2})|(http:\/{2})/, "")
            impedance.loadParameters(cur_path)
        }
    }

    FileDialog {
        id: savedDialog
        title: "Save File"
        selectExisting: false
        selectMultiple: false
        selectFolder: false
        modality: Qt.WindowModal
        onAccepted: {
            console.log(fileUrl.toString())

            var cur_path = fileUrl.toString()
            cur_path = cur_path.replace(
                        /^(file:\/{3})|(qrc:\/{2})|(http:\/{2})/, "")
            if (savedType == "parameters") {
                impedance.saveParameters(cur_path)
            } else if (savedType == "fitResults") {
                impedance.saveFitResults(cur_path)
            }

            selectExisting: false
            selectMultiple: false
            selectFolder: false
        }
        onRejected: {
            console.log("Rejected")
        }
    }
    FileDialog {
        id: fileDialog
        title: "Choose File"
        selectFolder: false
        onAccepted: {
            console.log("You choose: " + fileDialog.fileUrls)
            if (selectMultiple) {
                console.log("Select multiple")
                console.log(fileUrls.toString())
                for (var j = 0; j < fileUrls.length; j++) {
                    var cur_pathj = fileUrls[j].toString()
                    cur_pathj = cur_pathj.replace(
                                /^(file:\/{3})|(qrc:\/{2})|(http:\/{2})/, "")
                    ls_data = ls_data + cur_pathj + ";"
                }
                console.log(ls_data)
            } else {
                var cur_path = fileDialog.fileUrl.toString()
                // remove prefixed "file:///"
                cur_path = cur_path.replace(
                            /^(file:\/{3})|(qrc:\/{2})|(http:\/{2})/, "")
                dataPath.text = decodeURIComponent(cur_path)
            }
        }

        onRejected: {
            console.log("Rejected")
        }

        // Component.onCompleted: visible = true
    }

    GridLayout {
        id: gridLayout
        anchors.fill: parent
        columns: 1
        rows: 2

        Layout.fillHeight: true
        Layout.fillWidth: true
        anchors.top: mainView.top
        anchors.bottom: mainView.bottom
        anchors.left: mainView.left
        anchors.right: mainView.right

        Rectangle {
            id: rec01
            Layout.fillWidth: true
            height: 50

            RowLayout {
                anchors.left: parent.left
                anchors.leftMargin: 5
                Layout.fillHeight: true
                Layout.fillWidth: true
                anchors.verticalCenter: parent.verticalCenter
                anchors.top: parent.top

                ComboBox {
                    id: dataSelect
                    rightPadding: 0
                    antialiasing: true
                    implicitWidth: 325
                    flat: false
                    model: ["Phy-EIS"]
                    
                    padding: 0
                    background: Rectangle {
                        //                        border.color: "black"
                        border.width: 2
                        radius: 3
                        width: dataSelect.width
                    }
                    ToolTip.text: "Select data type (DX30, DX29, ...)"
                    ToolTip.visible: hovered
                }

                Button {
                    id: dataBtn
                    text: "<font color='#000000'> Data </font>"
                    padding: 5
                    Layout.maximumHeight: 30
                    Layout.maximumWidth: 60
                    onClicked: {
                        console.log("Open Data file")
                        switch (dataSelect.currentText) {
						
						case "Phy-EIS":
							fileDialog.title = "Please choose data for Phy-EIS"
                            fileDialog.selectMultiple = false
                            break
							
                        default:
                            dataMessageDialog.open()
                            break
                        }
                        fileDialog.open()
                    }
                }

                Button {
                    id: button
                    text: "Run Fit/Simulation"
                    Layout.maximumHeight: 30
                    padding: 5
                    highlighted: false
                    flat: false

                    states: State {
                        name: "brighter"
                        when: mouseArea.pressed
                        PropertyChanges {
                            target: rect
                            color: "yellow"
                        }
                    }
                    onClicked: {
                        console.log("Run fitting simualtion clicked")
                        switch (dataSelect.currentText) {
						
						case "Phy-EIS":
							console.log("Please choose data for Phy-EIS")
                            createDialogParameters("Phy-EIS", phy_eis_names,
                                                   phy_eis_values, phy_eis_fixed)
                            break
							
                        default:
                            console.log("Please select data")
                            break
                        }

                        fittingSimulationDialog.open()
                    }
                }

                Text {
                    id: dataPath
                    text: "Data Path:"
                }
            }
        }

        WebEngineView {
            Layout.fillHeight: true
            Layout.fillWidth: true
            id: graphView
            url: "https://sites.google.com/site/jnuelectroceramics/"
        }
    }
}
