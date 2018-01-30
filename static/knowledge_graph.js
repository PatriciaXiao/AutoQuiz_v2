function render_graph(roam) {
    var dom = document.getElementById("graph_container");
    var myChart = echarts.init(dom);
    var app = {};
    option = null;
    option = {
        title: {
            text: 'Graph sample'
        },
        tooltip: {},
        animationDurationUpdate: 1500,
        animationEasingUpdate: 'quinticInOut',
        series : [
            {
                type: 'graph',
                layout: 'none',
                symbolSize: 50,
                roam: roam,
                label: {
                    normal: {
                        show: true
                    }
                },
                edgeSymbol: ['circle', 'arrow'],
                edgeSymbolSize: [4, 10],
                edgeLabel: {
                    normal: {
                        textStyle: {
                            fontSize: 20
                        }
                    }
                },
                data: [{
                    name: 'node 1',
                    x: 300,
                    y: 300,
                    itemStyle: {
                        normal: {
                            color: "green",
                        }
                    }
                }, {
                    name: 'node 2',
                    x: 800,
                    y: 300
                }, {
                    name: 'node 3',
                    x: 550,
                    y: 100
                }, {
                    name: 'node 4',
                    x: 550,
                    y: 500
                }],
                // links: [],
                links: [{
                    source: 0,
                    target: 1,
                    symbolSize: [5, 20],
                    label: {
                        normal: {
                            show: true
                        }
                    },
                    lineStyle: {
                        normal: {
                            width: 5,
                            curveness: 0.2
                        }
                    }
                }, {
                    source: 'node 2',
                    target: 'node 1',
                    label: {
                        normal: {
                            show: true
                        }
                    },
                    lineStyle: {
                        normal: { curveness: 0.2 }
                    }
                }, {
                    source: 'node 1',
                    target: 'node 3'
                }, {
                    source: 'node 2',
                    target: 'node 3'
                }, {
                    source: 'node 2',
                    target: 'node 4'
                }, {
                    source: 'node 1',
                    target: 'node 4'
                }],
                lineStyle: {
                    normal: {
                        opacity: 0.9,
                        width: 2,
                        curveness: 0
                    }
                }/*,
                itemStyle: {
                    normal: {
                        color: "green",
                    }
                }*/
            }
        ]
    };
    if (option && typeof option === "object") {
        console.log(option.series[0].data)
        option.series[0].data.forEach(function (node) {
            console.log(node.itemStyle)
            /*
            node.itemStyle = {
                    normal: {
                        color: "green",
                    }
                };
                */
            console.log(node.itemStyle)
        })
        myChart.setOption(option, true);
        myChart.on('click', function (params) {
            request_exercise_section(1);
        })
    }
}