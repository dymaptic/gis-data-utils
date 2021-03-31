using Esri.ArcGISRuntime.Portal;
using Esri.ArcGISRuntime.Security;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;

namespace EditPortalItemDataApp
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window
    {
        private Dictionary<string, ArcGISPortal> _portalConnections = new Dictionary<string, ArcGISPortal>();

        public MainWindow()
        {
            InitializeComponent();
        }

        private async void GetItemDataButton_Click(object sender, RoutedEventArgs e)
        {
            PortalItem portalItem = null;

            try
            {
                // Get Portal connection parameters
                var itemId = ItemIdBox.Text;
                var portalUrl = PortalUrlBox.Text;

                // Make sure Portal URL and item ID are specified

                if (string.IsNullOrEmpty(portalUrl))
                {
                    ItemDataBox.Text = "Portal URL must be specified";
                    return;
                }

                if (string.IsNullOrEmpty(itemId))
                {
                    ItemDataBox.Text = "Portal Item ID must be specified";
                    return;
                }

                // Update status text to indicate operation in progress
                StatusText.Text = "Retrieving item data...";

                // Get the item and corresponding data for the specified Portal and item ID
                portalItem = await GetPortalItemAsync(portalUrl, itemId, UserNameBox.Text, PasswordBox.Password);
                var itemData = await portalItem.GetDataAsync();

                // Convert the item data from a stream into a string
                var itemDataString = string.Empty;
                using (var reader = new StreamReader(itemData))
                {
                    itemDataString = await reader.ReadToEndAsync();
                }

                try
                {
                    // Check whether the content is JSON by attempting to convert it into a JSON object
                    var itemDataJsonVal = JValue.Parse(itemDataString);

                    // Format the JSON and display it
                    var itemDataFormattedJson = itemDataJsonVal.ToString(Formatting.Indented);
                    ItemDataBox.Text = itemDataFormattedJson;
                }
                catch
                {
                    // Something went wrong when parsing or formatting the JSON, so just display the item content as-is
                    ItemDataBox.Text = itemDataString;
                }
            }
            catch (Exception ex)
            {
                // An unexpected error occurred - notify user
                StatusText.Text = "Error retrieving data";
                ItemDataBox.Text = $"Error while attempting to retrieve item data: {ex.Message}\n\nStack trace:\n{ex.StackTrace}";
                return;
            }

            // Update status text to show operation completion
            StatusText.Text = $"Data for item \"{portalItem.Title}\" (ID: {portalItem.ItemId}) retrieved successfully";
        }

        private async void UpdateDataButton_Click(object sender, RoutedEventArgs e)
        {
            PortalItem portalItem = null;

            try
            {
                // Get Portal connection parameters
                var itemId = ItemIdBox.Text;
                var portalUrl = PortalUrlBox.Text;

                // Make sure Portal URL and item ID are specified

                if (string.IsNullOrEmpty(portalUrl))
                {
                    ItemDataBox.Text = "Portal URL must be specified";
                    return;
                }

                if (string.IsNullOrEmpty(itemId))
                {
                    ItemDataBox.Text = "Portal Item ID must be specified";
                    return;
                }

                // Update status text to indicate operation in progress
                StatusText.Text = $"Updating data for item {itemId}...";

                // Get the item for the specified Portal and item ID
                portalItem = await GetPortalItemAsync(portalUrl, itemId, UserNameBox.Text, PasswordBox.Password);

                // Push the data in the item data textbox to the Portal item
                await portalItem.UpdateDataAsync(ItemDataBox.Text);
            }
            catch (Exception ex)
            {
                // An unexpected error occurred - notify user
                StatusText.Text = "Error updating data";
                ItemDataBox.Text = $"Error while attempting to retrieve item data: {ex.Message}\n\nStack trace:\n{ex.StackTrace}";
                return;
            }

            // Update status text to show operation completion
            StatusText.Text = $"Data for item \"{portalItem.Title}\" (ID: {portalItem.ItemId}) updated successfully";
        }

        private async Task<PortalItem> GetPortalItemAsync(string portalUrl, string itemId, string username, string password)
        {
            var key = $"{portalUrl};{username}";
            var portal = _portalConnections.ContainsKey(key) ? _portalConnections[key] : null;
            PortalItem item;

            // Connect to Portal
            var portalUri = new Uri(PortalUrlBox.Text);
            if (!string.IsNullOrEmpty(username) && !string.IsNullOrEmpty(password))
            {
                // Authenticate and then connect if user and password are specified
                var cred = await AuthenticationManager.Current.GenerateCredentialAsync(portalUri, username, password);
                portal = await ArcGISPortal.CreateAsync(portalUri, cred);
            }
            else
            {
                // Connect anonymously if user and/or password aren't specified
                portal = await ArcGISPortal.CreateAsync(portalUri);
            }

            _portalConnections[key] = portal;

            // Get the item for the specified ID
            item = await PortalItem.CreateAsync(portal, itemId);

            return item;
        }
    }
}
