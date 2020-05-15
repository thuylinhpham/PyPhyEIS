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
    title: qsTr("PyPhyEIS by Thuy Linh Pham")

    property int lastW: 0
    property int lastH: 0

    // Barsoukov-Pham-Lee_1D
    property var barsoukov_Pham_Lee_1_names: ["R_ohm", "Rm", "Rct", "Rd", "R_i", "C_dl", "C_d", "C_i", "Q_W"]
    property var barsoukov_Pham_Lee_1_values: ["6.16", "6.24", "13.869", "26.01", "96.9", "3.03e-7", "0.07", "1.032", "0.000336"]
    property var barsoukov_Pham_Lee_1_fixed: [1, 1, 1, 1, 1, 1, 1, 1, 1]
	
    // Barsoukov-Pham-Lee_2D
    property var barsoukov_Pham_Lee_2_names: ["R_ohm", "Rm", "Rct", "Rd", "R_i", "C_dl", "C_d", "C_i", "Q_W"]
    property var barsoukov_Pham_Lee_2_values: ["6.16", "6.24", "6.934", "26.01", "96.9", "6.07e-7", "0.07", "1.032", "0.000336"]
    property var barsoukov_Pham_Lee_2_fixed: [1, 1, 1, 1, 1, 1, 1, 1, 1]

    // Barsoukov-Pham-Lee_3D
    property var barsoukov_Pham_Lee_3_names: ["R_ohm", "Rm", "Rct", "Rd", "R_i", "C_dl", "C_d", "C_i", "Q_W"]
    property var barsoukov_Pham_Lee_3_values: ["6.16", "6.24", "4.623", "26.01", "96.9", "9.1e-7", "0.07", "1.032", "0.000336"]
    property var barsoukov_Pham_Lee_3_fixed: [1, 1, 1, 1, 1, 1, 1, 1, 1]

    property string dialogCreated: ""

    property real pressX: 0.0
    property real pressY: 0.0
    property real releaseX: 0.0
    property real releaseY: 0.0
    property bool pressHold: false
    property bool runFit: false

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
            var add_text = ""
            
            if (runFit)
                add_text = "Fitting"
            else
                add_text = "Simulation"
            
            runBtn.text = "Run " + add_text
			
			runBtn.enabled = true
			resetParameters.enabled = true
            
            runsimbtn.enabled = true
            runfitbtn.enabled = true
            freqrangebtn.enabled = true
            if (fit_status == 1) {
                fitStatus.text = "Success"
                saveParameters.enabled = true
                saveFitResults.enabled = true
            } else {
                saveParameters.enabled = false
                saveFitResults.enabled = false
                if (fit_status == 0) {
                    fitStatus.text = "Failed " + add_text
                } else {
                    fitStatus.text = "Stopped " + add_text
                }
            }
        }

        onChiSquare: {
            chisqr.text = chiSquare_Val
            //redChisqr.text = redChiSquare_Val
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
        }
    }

    // Load initial values
    function loadValues(param_names, best_params, error_fit, error_fit_percent, par_frees) {
        console.log("Load values")
        console.log(best_params)
        for (var pj = 1; pj < gridDialog.children.length; pj++) {
			for (var i = 1; i <= param_names.length; i++) {
				// console.log('CK :', pj, gridDialog.children.length, gridDialog.children[pj].children[0].children[0].text, param_names[i-1])
				if (gridDialog.children[pj].children[0].children[0].text.toLowerCase() === param_names[i-1].toLowerCase())  {
					gridDialog.children[pj].children[1].children[0].text = best_params[i - 1]
					gridDialog.children[pj].children[1].children[0].cursorPosition = 0
					gridDialog.children[pj].children[3].children[0].text = error_fit[i - 1]
					gridDialog.children[pj].children[4].children[0].text = error_fit_percent[i - 1]

					if (par_frees[i-1] === 1)    {
						gridDialog.children[pj].children[2].checked = true
						gridDialog.children[pj].children[1].children[0].readOnly = false
					}
					else    {
						gridDialog.children[pj].children[2].checked = false
						gridDialog.children[pj].children[1].children[0].readOnly = true
					}
					// console.log('Assign :', pj, gridDialog.children.length, gridDialog.children[pj].children[0].children[0].text, param_names[i-1])
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
        if (runFit)
            fittingSimulationDialog.title = "Fitting " + model_name
        else
            fittingSimulationDialog.title = "Simulation " + model_name
        
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
                        implicitWidth: 125
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
                        width: 100
                        height: fitMethod.height
                        color: "transparent"
                        Text {
                            id: fitStatus
                            text: ""
							color: "blue"
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
                            text: "Sum of Square:"
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
                    Layout.minimumWidth: 300
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
                            columns: 2
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
                                }
                            }

                            Button {
                                id: runBtn
                                text: "Run"
                                Layout.maximumHeight: 30
                                
                                Layout.fillWidth: true
                                onClicked: {
                                    fit_log_text.text = ""
                                    if (runBtn.text == "Stop Fitting") {
                                        console.log("Stop fitting")
                                        fitStatus.text = "Stopping"
                                        impedance.stop_fitting()
                                    }
                                    else if (runBtn.text == "Stop Simulation")  {
                                        console.log("Stop Simulation")
                                        fitStatus.text = "Stopping"
                                        impedance.stop_fitting()
                                    }
                                    else if ((runFit || parseInt(numPerDecade.text) <= 0) && dataPath.text === "Data Path:"
                                                && ls_data == "") {
                                            fitStatusDialog.text = "Please choose impedance data file"
                                            fitStatusDialog.open()
                                        } else {
                                            var send_names = []
                                            var send_vals = []
                                            var send_fixed = []
                                            var send_freq_range = [minFreq.text, maxFreq.text, numPerDecade.text]
                                            var cur_strings = ""
                                            var cur_isFixed = ""
                                            var cur_name = ""
                                            var send_mdl = modelSelect.currentText
                                            var send_data = dataPath.text
                                            var cur_method = fitMethod.currentText
                                            var send_op = 0

                                            var count_free = 0
                                            for (var i = 1; i < gridDialog.children.length; i++) {
                                                cur_name = gridDialog.children[i].children[0].children[0].text.toLowerCase()
                                                cur_strings = gridDialog.children[i].children[1].children[0].text
                                                cur_isFixed = gridDialog.children[i].children[2].checked ? 0 : 1
                                                send_vals.push(cur_strings)
                                                send_fixed.push(cur_isFixed)
                                                send_names.push(cur_name)
                                                if (cur_isFixed == 0)
                                                    count_free = count_free + 1
                                            }

                                            if (count_free == 0 && runFit)    {
                                                fitStatusDialog.text = "Need at least 1 free parameter."
                                                fitStatusDialog.open()
                                            }
                                            else    {
                                                fitStatus.text = "Running"
                                                if (fileDialog.selectMultiple) {
                                                    send_data = ls_data
                                                }

                                                if (runFit) {
                                                    runBtn.text = "Stop Fitting"
                                                    send_op = 1
                                                }
                                                else    {
                                                    runBtn.text = "Stop Simulation"
                                                    send_op = 2
                                                }

                                                resetParameters.enabled = false
                                                
                                                saveParameters.enabled = false
                                                saveFitResults.enabled = false
                                                runsimbtn.enabled = false
                                                runfitbtn.enabled = false
                                                freqrangebtn.enabled = false

                                                impedance.fitting(
                                                            send_names, send_vals,
                                                            send_fixed, send_mdl,
                                                            wgtMethod.currentIndex,
                                                            fitMethod.currentText,
                                                            send_data, send_op, 0, send_freq_range)
                                            }
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

    MessageDialog {
        id: aboutme
        title: qsTr("About")
        text: "PyPhyEIS by Thuy Linh Pham"
        icon: StandardIcon.Information
    }

    menuBar: MenuBar {
        objectName: "abc"
        Menu {
            title: "Home"
            Action {text: qsTr("ECL homepage"); onTriggered: {graphView.url=""; graphView.url="https://sites.google.com/site/jnuelectroceramics/"}}
        }

        Menu {
            title: "Help"
            Action {text: qsTr("About"); onTriggered: aboutme.open()}
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
        rows: 5

        Layout.fillHeight: true
        Layout.fillWidth: true
        anchors.top: mainView.top
        anchors.bottom: mainView.bottom
        anchors.left: mainView.left
        anchors.right: mainView.right
        rowSpacing: 5
        Rectangle {
            id: rec01
            Layout.fillWidth: true
            height: 35
            
            anchors.bottomMargin: 0
            RowLayout {
                id: md_data_layout
                anchors.left: parent.left
                anchors.leftMargin: 5
                Layout.fillHeight: true
                Layout.fillWidth: true
                anchors.verticalCenter: parent.verticalCenter
                anchors.top: parent.top

                // Model selection
                ComboBox {
                    id: modelSelect
                    rightPadding: 0
                    antialiasing: true
                    implicitWidth: 325
                    flat: false
                    model: ["Barsoukov-Pham-Lee_1D", "Barsoukov-Pham-Lee_2D", "Barsoukov-Pham-Lee_3D"]
                    
                    padding: 0
                    background: Rectangle {
                        border.width: 2
                        radius: 3
                        width: modelSelect.width
                    }
                    ToolTip.text: "Select data type"
                    ToolTip.visible: hovered
                }

                // Select and load impedance data file
                Button {
                    id: dataBtn
                    text: "<font color='#000000'> Data </font>"
                    padding: 5
                    Layout.maximumHeight: 30
                    Layout.maximumWidth: 60
                    onClicked: {
                        console.log("Open Data file")
                        switch (modelSelect.currentText) {

                        case "Barsoukov-Pham-Lee_1D":
                            fileDialog.title = "Please choose data for Barsoukov-Pham-Lee_1D"
                            fileDialog.selectMultiple = false
                            break

                        case "Barsoukov-Pham-Lee_2D":
                            fileDialog.title = "Please choose data for Barsoukov-Pham-Lee_2D"
                            fileDialog.selectMultiple = false
                            break

                        case "Barsoukov-Pham-Lee_3D":
                            fileDialog.title = "Please choose data for Barsoukov-Pham-Lee_3D"
                            fileDialog.selectMultiple = false
                            break

                        default:
                            dataMessageDialog.open()
                            break
                        }
                        fileDialog.open()
                    }
                }

                Text {
                    id: dataPath
                    text: "Data Path:"
                }
            }
        }

        Rectangle   {
            id: rec02
            Layout.fillWidth: true
            height: 35
            anchors.topMargin: 0
            anchors.bottomMargin: 0
            
            RowLayout   {
                anchors.left: parent.left
                //anchors.leftMargin: modelSelect.width + 2*md_data_layout.spacing
                anchors.leftMargin: 5
                Layout.fillHeight: true
                Layout.fillWidth: true
                anchors.verticalCenter: parent.verticalCenter
                anchors.top: parent.top
                anchors.topMargin: 0
                //anchors.bottomMargin: 0
                Button {
                    id: runfitbtn
                    text: "Fit"
                    Layout.maximumHeight: 30
                    Layout.maximumWidth: 60
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
                        runFit = true
                        fitMethod.visible = true
                        wgtMethod.visible = true
                        console.log("Run fitting simualtion clicked")
                        switch (modelSelect.currentText) {
                        
                        case "Barsoukov-Pham-Lee_1D":
                            console.log("Please choose data for Barsoukov-Pham-Lee_1D")
                            createDialogParameters("Barsoukov-Pham-Lee_1D", barsoukov_Pham_Lee_1_names,
                                                    barsoukov_Pham_Lee_1_values, barsoukov_Pham_Lee_1_fixed)
                            break

                        case "Barsoukov-Pham-Lee_2D":
                            console.log("Please choose data for Barsoukov-Pham-Lee_2D")
                            createDialogParameters("Barsoukov-Pham-Lee_2D", barsoukov_Pham_Lee_2_names,
                                                    barsoukov_Pham_Lee_2_values, barsoukov_Pham_Lee_2_fixed)
                            break

                        case "Barsoukov-Pham-Lee_3D":
                            console.log("Please choose data for Barsoukov-Pham-Lee_3D")
                            createDialogParameters("Barsoukov-Pham-Lee_3D", barsoukov_Pham_Lee_3_names,
                                                    barsoukov_Pham_Lee_3_values, barsoukov_Pham_Lee_3_fixed)
                            break

                        default:
                            console.log("Please select data")
                            break
                        }
                        runBtn.text = "Run Fitting"
                        fittingSimulationDialog.open()
                    }
                }

                Button {
                    id: runsimbtn
                    text: "Simulation"
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
                        runFit = false
                        fitMethod.visible = false
                        wgtMethod.visible = false
                        console.log("Run fitting simualtion clicked")
                        switch (modelSelect.currentText) {
                        
                        case "Barsoukov-Pham-Lee_1D":
                            console.log("Please choose data for Barsoukov-Pham-Lee_1D")
                            createDialogParameters("Barsoukov-Pham-Lee_1D", barsoukov_Pham_Lee_1_names,
                                                    barsoukov_Pham_Lee_1_values, barsoukov_Pham_Lee_1_fixed)
                            break

                        case "Barsoukov-Pham-Lee_2D":
                            console.log("Please choose data for Barsoukov-Pham-Lee_2D")
                            createDialogParameters("Barsoukov-Pham-Lee_2D", barsoukov_Pham_Lee_2_names,
                                                    barsoukov_Pham_Lee_2_values, barsoukov_Pham_Lee_2_fixed)
                            break

                        case "Barsoukov-Pham-Lee_3D":
                            console.log("Please choose data for Barsoukov-Pham-Lee_3D")
                            createDialogParameters("Barsoukov-Pham-Lee_3D", barsoukov_Pham_Lee_3_names,
                                                    barsoukov_Pham_Lee_3_values, barsoukov_Pham_Lee_3_fixed)
                            break

                        default:
                            console.log("Please select data")
                            break
                        }
                        runBtn.text = "Run Simulation"
                        fittingSimulationDialog.open()
                    }
                }
                Button {
                    id: freqrangebtn
                    text: "Frequency range"
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
                        console.log("Frequency range clicked")
                        minFreq.readOnly = !minFreq.readOnly
                        maxFreq.readOnly = !maxFreq.readOnly
                        numPerDecade.readOnly = !numPerDecade.readOnly
                        if (minFreq.readOnly == true) {
                            highlighted = false
                            minFreqRec.color = 'gainsboro'
                            maxFreqRec.color = 'gainsboro'
                            numPerDecadeRec.color = 'gainsboro'
                            minFreq.selectByMouse = false
                            maxFreq.selectByMouse = false
                            numPerDecade.selectByMouse = false
                        }
                        else {
                            highlighted = true 
                            minFreqRec.color = 'white'
                            maxFreqRec.color = 'white'
                            numPerDecadeRec.color = 'white'
                            minFreq.selectByMouse = true
                            maxFreq.selectByMouse = true
                            numPerDecade.selectByMouse = true
                        }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 35
            anchors.topMargin: 0
            anchors.bottomMargin: 0
            id: rec04
            RowLayout {
                anchors.left: parent.left
                anchors.leftMargin: 5
                Layout.fillHeight: true
                Layout.fillWidth: true
                anchors.verticalCenter: parent.verticalCenter
                anchors.top: parent.top
                anchors.topMargin: 0
                Text {
                    text: "Minimum (Hz)"
                    font.bold: false
                }
                Rectangle {
                    id: minFreqRec
                    width:100;
                    height:20;
                    color: "gainsboro";
                    border.color:"black"; 
                    TextInput {
                        id: minFreq
                        text: '1e-6'
                        readOnly:true;
                        cursorVisible: false; 
                        selectionColor: "green";
                        selectByMouse: false;
                        clip: true;
                        font.pixelSize: 12;
                        anchors.left: 
                        parent.left;
                        anchors.bottom:parent.bottom;
                        leftPadding: 5;
                        rightPadding:5; 
                        bottomPadding:2; 
                        width:95

                        
                    }
                }
                Text {
                    text: "Maximum (Hz)"
                    font.bold: false
                }
                Rectangle {
                    id: maxFreqRec
                    width:100;
                    height:20;
                    color: "gainsboro";
                    border.color:"black"; 
                    TextInput {
                        id: maxFreq
                        text: '1e6'
                        readOnly:true; 
                        cursorVisible: false; 
                        selectionColor: "green";
                        selectByMouse: false;
                        clip: true;
                        font.pixelSize: 12;
                        anchors.left: 
                        parent.left;
                        anchors.bottom:parent.bottom;
                        leftPadding: 5;
                        rightPadding:5; 
                        bottomPadding:2; 
                        width:95
                    }
                }
                Text {
                    text: "Number per decade"
                    font.bold: false
                }
                Rectangle {
                    id: numPerDecadeRec
                    width:100;
                    height:20;
                    color: "gainsboro";
                    border.color:"black"; 
                    TextInput {
                        id: numPerDecade
                        text: '10'
                        readOnly:true; 
                        cursorVisible: false; 
                        selectionColor: "green";
                        selectByMouse: false;
                        clip: true;
                        font.pixelSize: 12;
                        anchors.left: 
                        parent.left;
                        anchors.bottom:parent.bottom;
                        leftPadding: 5;
                        rightPadding:5; 
                        bottomPadding:2; 
                        width:95
                    }
                }
            }
        }
        WebEngineView {
            Layout.fillHeight: true
            Layout.fillWidth: true
            id: graphView
            url: "https://sites.google.com/site/jnuelectroceramics/"
            // onLoadingChanged: {
            //     if (loading == false)
            //         loading_indicator.running = false
            //     else
            //         loading_indicator.running = true
            // }

        }
        BusyIndicator{
            id: loading_indicator
            anchors.centerIn: parent
            running: graphView.loading === true
            palette.dark: "blue"
        }
    }
}
